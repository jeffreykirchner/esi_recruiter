from datetime import datetime, timedelta, timezone

import logging
import pytz
import uuid
import json

from django.db import models
from django.contrib.auth.models import User
from django.db.models import F, Q, When, Case
from django.contrib import admin
from django.db.models import Subquery, OuterRef
from django.core.serializers.json import DjangoJSONEncoder

from main.models import institutions
from main.models import parameters
from main.models import experiment_sessions
from main.models import profile
from main.models import AccountTypes
from main.models import schools
from main.models import majors
from main.models import genders
from main.models import subject_types

from . import email_filters

import main

from django.dispatch import receiver
from django.db.models.signals import post_delete

#user profile, extending the user model
class profile(models.Model):

    user = models.OneToOneField(User, verbose_name="User", on_delete=models.CASCADE)
    type = models.ForeignKey(AccountTypes, verbose_name="Account Type", on_delete=models.CASCADE,default=2)            #subject or staff
    school = models.ForeignKey(schools, verbose_name="School", on_delete=models.CASCADE,default=1)                      #Chapman University ETC
    major = models.ForeignKey(majors, verbose_name="Major", on_delete=models.CASCADE,default=1)                         #Economics ETC
    gender = models.ForeignKey(genders, verbose_name="Gender", on_delete=models.CASCADE,default=1)
    subject_type = models.ForeignKey(subject_types, verbose_name="Subject Type", on_delete=models.CASCADE,default=1)                #Undergrad, grad, non student
    email_filter = models.ForeignKey(email_filters, verbose_name="Email Filter", on_delete=models.CASCADE,null=True,blank=True)     #email filters that apply to this user
    
    studentID = models.CharField(verbose_name="ID Number", max_length=100, default="00000000", null=True, blank=True) #student ID number
    email_confirmed =  models.CharField(verbose_name="Email Confirmed", max_length = 100, default="no")               #yes/code/no
    blackballed = models.BooleanField(verbose_name="Blackballed", default=False)                                      #if a subject is blackballed they will not be auto recruited
    phone = models.CharField(verbose_name="Phone Number", max_length = 100, default="")                               #phone number of subject
    studentWorker = models.BooleanField(verbose_name="Student Woker", default=False)                                  #true is subject is a student worker
    paused = models.BooleanField(verbose_name="Paused", default=False)                                                #allows subject to pause getting invitations
    w9Collected = models.BooleanField(verbose_name="W9 Form Collected", default=False)                                #true if a w9 tax form was collected from subject
    international_student = models.BooleanField(verbose_name="International Student", default=False)                  #true if subject is an international student
    
    mfa_hash = models.CharField(verbose_name="Multi-factor Hash", max_length = 50, null=True, blank=True)             #hash for multi-factor authentication
    mfa_required = models.BooleanField(verbose_name="Multi-factor Required", default=False)                           #true if multi-factor authentication is required
    mfa_setup_complete = models.BooleanField(verbose_name="Multi-factor Setup Complete", default=False)               #true if multi-factor authentication is setup
    
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)                                     #publicly sharable id number for subjects

    #consent_required_legacy = models.BooleanField(verbose_name="Consent Form Required", default=True)                #true if the subject must agree to the current consent form (used before session by session consent forms)

    send_daily_email_report = models.BooleanField(verbose_name="Send Daily Email Report", default=False)              #if true, send daily report of the past day's activity
    can_paypal = models.BooleanField(verbose_name="User can send PayPal payments", default=False)                     #if true, user can send PayPal Payments
    can_recruit = models.BooleanField(verbose_name="User can recruit subjects to sessions", default=False)            #if true, user can recruit subjects to sessions
    pi_eligible = models.BooleanField(verbose_name="User can be a PI", default=False)                                  #if true, user can be a PI

    disabled = models.BooleanField(verbose_name="Disabled", default=False)                                             #if true, user is disabled and cannot login

    password_reset_key = models.UUIDField(verbose_name='Password Reset Key', null=True, blank=True)                   #log in key used to reset subject password

    timestamp = models.DateTimeField(verbose_name="Created On", auto_now_add=True)
    updated = models.DateTimeField(verbose_name="Updated On", auto_now=True)

    def __str__(self):
        return "%s, %s | Student ID: %s" % (self.user.last_name,self.user.first_name,self.studentID)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
        ordering = ['user__last_name', 'user__first_name']

    
    @admin.display(ordering='user__last_login')
    def last_login(self):
        return self.user.last_login
    
    #return the last login time in the server's time zone
    def last_login_tz(self):
        p = parameters.objects.first()
        if not self.user.last_login:
            return "Never"
        return self.user.last_login.astimezone(pytz.timezone(p.subjectTimeZone)).strftime("%m/%d/%Y %I:%M %p %Z")

    #find which email filter, if any applies to user
    def setup_email_filter(self):
        logger = logging.getLogger(__name__) 
        logger.info("set email filter")
        
        self.email_filter = None
        self.save()

        if not "@" in self.user.email:
            return 0

        email_split = self.user.email.split("@")

        #logger.info(email_split)

        #domain__regex = r'.+@' + email_regx
        ef = email_filters.objects.filter(domain = email_split[1]).first()

        if ef:
            self.email_filter = ef
            self.save()
            return 1
        else:
            return 0

    #get a list of session days the subject has participated in or was bumped from
    def sorted_session_day_list_earningsOnly(self):
        logger = logging.getLogger(__name__) 

        qs=self.user.ESDU.filter(Q(attended=True)|Q(bumped=True)) \
                                 .annotate(date=F('experiment_session_day__date')).order_by('-date')

        out_str = [e.json_subjectInfo() for e in qs]    

        logger.info("get attended session day list")
        #logger.info(out_str)

        return out_str

    #get the query set of upcoming session days for this subject
    def sorted_session_day_upcoming(self, confirmedOnly):
        logger = logging.getLogger(__name__) 
        #logger.info("sorted session day upcoming")

        tz = pytz.utc

        #logger.info(tz)

        t = datetime.now(tz)
        t = t.replace(hour=0, minute=0, second=0)

        #logger.info(t)

        qs=self.user.ESDU.annotate(date=F('experiment_session_day__date'))\
                         .annotate(session_id=F('experiment_session_day__experiment_session__id'))\
                         .order_by('-date')\
                         .filter(date__gte = t)\
                         .filter(experiment_session_day__complete = False)
        
        if confirmedOnly:
            qs=qs.filter(confirmed=True)
        
        return qs
    
    #get a list of upcoming experiments for this subject
    def sorted_session_day_list_upcoming(self,confirmedOnly):
        logger = logging.getLogger(__name__) 

        qs =self.sorted_session_day_upcoming(confirmedOnly)

        out_lst = [e.json_subjectInfo() for e in qs]      

        #logger.info("get upcoming session day list")
        #logger.info(out_str)

        return out_lst

    #upcoming session query set
    def sessions_upcoming(self,confirmedOnly,startDateRange):
        logger = logging.getLogger(__name__)

        qs = self.sorted_session_day_upcoming(confirmedOnly)

        session_ids = qs.values_list('experiment_session_day__experiment_session__id',flat=True).distinct()

        es = experiment_sessions.objects.annotate(first_date=models.Min("ESD__date"))\
                                        .annotate(last_date=models.Max("ESD__date"))\
                                        .filter(id__in = session_ids)\
                                        .filter(last_date__gte = startDateRange)
    
        return es

    #sorted json list of session a subject is in
    def sorted_session_list_upcoming(self):
        logger = logging.getLogger(__name__) 

        session_list = self.sessions_upcoming(False, datetime.now(pytz.utc) - timedelta(hours=1))

        # logger.info(f"consent_form_list: {consent_form_list}")

        out_lst = [es.json_subject(self.user) for es in session_list.all()
                                    .annotate(first_date=models.Min("ESD__date"))                                    
                                    .order_by('-first_date')]

        return out_lst

    #get sorted list of traits
    def sorted_trait_list(self):
        logger = logging.getLogger(__name__) 

        pt_list = self.profile_traits.filter(trait__archived=False)

        return [pt.json() for pt in pt_list]

    #get full invitation list
    def sorted_session_day_list_full(self):
        logger = logging.getLogger(__name__) 
    
        qs = self.user.ESDU.annotate(date=F('experiment_session_day__date'))\
                           .order_by('-date')

        out_str = [e.json_subjectInfo() for e in qs]      

        logger.info("get full invitation history")
        #logger.info(out_str)

        return out_str

    #get list of institutions this subject has been in
    def get_institution_list(self):
        l = institutions.objects.none()
        out_str = []
        esdus = self.user.ESDU.filter(attended=True)

        for i in esdus:
            l |= i.experiment_session_day.experiment_session.experiment.institution.all()                

        logger = logging.getLogger(__name__)
        logger.info("get institution list")

        if len(l)>0:          
            out_str = [e.json() for e in l.distinct().order_by("name")]

        logger.info(out_str)

        return out_str

    #get list of notes made about user
    def get_notes(self):
        logger = logging.getLogger(__name__)
        logger.info("get note list")

        note_list=self.profile_note_set.all().order_by('-timestamp')

        return [n.json() for n in note_list]

    #return true if subject was bumped from last session they attended
    def bumped_from_last_session(self,excludeESDU):
        logger = logging.getLogger(__name__)
        #logger.info("Get bumped from last session")

        d = datetime.now(timezone.utc)
        ESDU_last = self.user.ESDU.exclude(id = excludeESDU).filter(confirmed = True,experiment_session_day__date__lt = d).order_by("-experiment_session_day__date").first()

        if ESDU_last:        
            if ESDU_last.bumped:
                # logger.info("Bumped from last: User " + str(self.user.id) + ", date " +  str(ESDU_last.experiment_session_day.date))
                return True
            else:
                return False
        else:
            return False

    #ytd payouts
    def get_ytd_payouts(self):
        logger = logging.getLogger(__name__)
        logger.info("ytd earnings")

        p = parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)

        #create a new tz aware date time
        s_date = datetime.now(tz)

        #replace with non aware info
        s_date = s_date.replace(day=1,month=1, hour=0,minute=0,second=0,microsecond=1)

        r1 = main.models.experiment_session_day_users.objects.filter(attended = True)\
                                                             .filter(experiment_session_day__date__gte = s_date)\
                                                             .filter(user = self.user)
                                                                  
                                            #  .annotate(totalBumps = Sum(Case(When(experiment_session_day_users__bumped = 1,
                                            #                                    then = 'experiment_session_day_users__show_up_fee'),
                                            #                                  When(experiment_session_day_users__attended = 1,
                                            #                                    then = 'experiment_session_day_users__show_up_fee'),
                                            #                                  default=Value(0)  )))\
                                            #  .filter(account__in = dpt.accounts_set.all(),
                                            #          date__gte=s_date,
                                            #          date__lte=e_date)\
                                            #  .filter(Q(totalEarnings__gt = 0) | 
                                            #          Q(totalBumps__gt = 0))\
                                            #  .select_related('experiment_session__experiment','account')\
                                            #  .order_by('date')
        r2 = main.models.experiment_session_day_users.objects.filter(bumped = True)\
                                                             .filter(experiment_session_day__date__gte = s_date)\
                                                             .filter(user = self.user)

        total_earnings = 0
        total_bumps = 0 

        for i in r1:
            total_earnings += i.earnings
            total_bumps += i.show_up_fee

        for i in r2:
            total_bumps += i.show_up_fee 

        logger.info(r1)
        logger.info(r2)
        
        temp_e = total_earnings + total_bumps

        return "$" + f'{temp_e:.2f}'

    #return true if adding user to session creates recruitment violations in other future  accepted experiments
    def check_for_future_constraints(self, es, first_date, i_list, experiment_id):
        logger = logging.getLogger(__name__)
        #logger.info("check for future constraints")

        qs_attending = self.sessions_upcoming(True, first_date)

        #ignore canceled experiment
        qs_attending = qs_attending.filter(canceled=False)

        #i_list = es.experiment.institution.values_list("id", flat=True)

        for s in qs_attending:
            user_list_valid = s.getValidUserList([{'id':self.user.id}], False, experiment_id, es.id, i_list, False)
            user_list_valid = s.getValidUserListDjango(user_list_valid, False, experiment_id, es.id, i_list, False)

            if not self.user in user_list_valid:
                #logger.info("Invitation failed attended recruitment violation")             
                logger.info(f'check_for_future_constraints Invitation failed attended recruitment violation User: {self.user.id} {self.user.email}, attending session: {s.id} violation experiment: {experiment_id}')
                return True
                        
        return False

    #check if use has consent form
    def check_for_consent(self, consent_form):
        if not consent_form:
            return True
        
        if not consent_form.agreement_required:
            return True

        consent_forms = self.profile_consent_forms_a.values_list('consent_form__id', flat=True)

        if consent_form.id in consent_forms:
            return True
        
        return False
    
    def check_for_consent_attended(self, consent_form):
        if not consent_form:
            return True
        
        if not consent_form.agreement_required:
            return True

        #consent_forms = self.profile_consent_forms_a.values_list('consent_form__id', flat=True)

        #if only bumped from consent form, require resign
        attended_consents = main.models.experiment_session_day_users.objects.filter(
                                                user__profile=self, 
                                                attended=True, 
                                                experiment_session_day__experiment_session__consent_form__id=consent_form.id)

        if len(attended_consents) > 0:
            return True
        
        return False
    
    def consent_signature(self, consent_form):

        if not consent_form:
            return None
       
        consent_form = self.profile_consent_forms_a.filter(consent_form__id=consent_form.id)

        if not consent_form:
            return None

        return consent_form.first().json() 
    
    #return list of missing umbrella consents
    def get_required_umbrella_consents(self):

        consent_forms = self.profile_consent_forms_a.values_list('consent_form__id', flat=True)
        missing_umbrella_consents = main.models.UmbrellaConsentForm.objects.filter(active=True) \
                                                                   .exclude(consent_form__id__in=consent_forms) 

        return [i.json() for i in missing_umbrella_consents]

    #return list of umbrella consents
    def get_umbrella_consents(self):

        umbrella_consent_forms = main.models.UmbrellaConsentForm.objects.all().values_list('consent_form__id', flat=True)
        
        consent_forms = self.profile_consent_forms_a.filter(consent_form__id__in=umbrella_consent_forms)
                                                                   
        return [{"id":i.id,
                "umbrella_consent_form":  main.models.UmbrellaConsentForm.objects.filter(consent_form__id=i.consent_form.id).values('id','display_name').first(),
                "date_string" : i.get_date_string_tz_offset(),
                } for i in consent_forms]


    #json version of model, small
    def json_min(self):
        return{
            "id":self.user.id,                        
            "first_name":self.user.first_name.capitalize(),   
            "last_name":self.user.last_name.capitalize(), 
            "email":self.user.email,
            "studentID":self.studentID,                 
        }

    #json version of model, full
    def json(self):
        return{
            "id":self.user.id,                        
            "first_name":self.user.first_name.capitalize(),   
            "last_name":self.user.last_name, 
            "email":self.user.email,
            "studentID":self.studentID, 
            "type":self.type.json(),  
            "gender":self.gender.json(),
            "email_confirmed":self.email_confirmed,  
            "blackballed":self.blackballed,         
        }
    
    def json_for_user_info(self):

        return{
            "id":self.user.id,                        
            "first_name":self.user.first_name.capitalize(),   
            "last_name":self.user.last_name.capitalize(), 
            "email":self.user.email,
            "studentID":self.studentID, 
            "type":self.type.id,
            "pi_eligible":1 if self.pi_eligible else 0,
            "studentWorker":1 if self.studentWorker else 0,
            "blackballed":1 if self.blackballed else 0,
            "paused":1 if self.paused else 0,
            "international_student":1 if self.international_student else 0,
            "can_paypal":1 if self.can_paypal else 0,
            "can_recruit":1 if self.can_recruit else 0,
            "disabled":1 if self.disabled else 0,
        }

    def json_for_profile_update(self):
        message = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'chapman_id': self.user.profile.studentID,
            'email': self.user.email,
            'gender': self.user.profile.gender.id,
            'phone': self.user.profile.phone,
            'major': self.user.profile.major.id,
            'subject_type': self.user.profile.subject_type.id,
            'studentWorker': 1 if self.user.profile.studentWorker else 0,
            'paused': 1 if self.user.profile.paused else 0,
            'password1':"",
            'password2':"",
        }

        return json.dumps(message, cls=DjangoJSONEncoder)

#delete associated user model when profile is deleted
@receiver(post_delete, sender=profile)
def post_delete_user(sender, instance, *args, **kwargs):
    if instance.user: # just in case user is not specified
        instance.user.delete()