from django.db import models
import logging
import traceback
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db.models import F,Q

from main.models import *
from main.models import institutions,parameters,experiment_sessions
from . import email_filters

import main

from django.dispatch import receiver
from django.db.models.signals import post_delete

from datetime import date
from datetime import datetime, timedelta,timezone
import pytz

import logging

#user profile, extending the user model
class profile(models.Model):

    user = models.OneToOneField(User,verbose_name="User", on_delete=models.CASCADE)
    type =  models.ForeignKey(account_types,verbose_name="Account Type",on_delete=models.CASCADE,default=2)            #subject or staff
    school = models.ForeignKey(schools,verbose_name="School",on_delete=models.CASCADE,default=1)                      #Chapman University ETC
    major = models.ForeignKey(majors,verbose_name="Major",on_delete=models.CASCADE,default=1)                         #Economics ETC
    gender = models.ForeignKey(genders,verbose_name="Gender",on_delete=models.CASCADE,default=1)
    subject_type = models.ForeignKey(subject_types,verbose_name="Subject Type",on_delete=models.CASCADE,default=1)                #Undergrad, grad, non student
    email_filter = models.ForeignKey(email_filters, verbose_name="Email Filter",on_delete=models.CASCADE,null=True,blank=True)     #email filters that apply to this user

    chapmanID = models.CharField(verbose_name="ID Number",max_length = 100,default="00000000")                       #student ID number
    email_confirmed =  models.CharField(verbose_name="Email Confirmed",max_length = 100,default="no")                 #yes/code/no
    blackballed = models.BooleanField(verbose_name="Blackballed",default=False)                                      #if a subject is blackballed they will not be auto recruited
    phone = models.CharField(verbose_name="Phone Number",max_length = 100,default="")                                #phone number of subject
    studentWorker = models.BooleanField(verbose_name="Student Woker",default=False)                                  #true is subject is a student worker
    paused = models.BooleanField(verbose_name="Paused",default=False)                                                #allows subject to pause getting invitations
    w9Collected = models.BooleanField(verbose_name="W9 Form Collected",default=False)                                #true if a w9 tax form was collected from subject
    nonresidentAlien = models.BooleanField(verbose_name="Nonresident Alien",default=False)                           #true is subject is a not a US Citizen or US Resident

    consentRequired = models.BooleanField(verbose_name="Consent Form Required",default=True)                         #true if the subject must agree to the current consent form  

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return "%s, %s | Chapman ID: %s" % (self.user.last_name,self.user.first_name,self.chapmanID)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

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
    def sorted_session_day_upcoming(self,confirmedOnly):
        logger = logging.getLogger(__name__) 
        logger.info("sorted session day upcoming")

        tz = pytz.utc

        #logger.info(tz)

        t = datetime.now(tz)
        t = t.replace(hour=0,minute=0, second=0)

        #logger.info(t)

        qs=self.user.ESDU.annotate(date=F('experiment_session_day__date'))\
                         .annotate(session_id=F('experiment_session_day__experiment_session__id'))\
                         .order_by('-date')\
                         .filter(date__gte = t)
        
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

        session_list = self.sessions_upcoming(False,datetime.now(pytz.utc)- timedelta(hours=1))

        out_lst = [es.json_subject(self.user) for es in session_list.all()
                                    .annotate(first_date=models.Min("ESD__date"))
                                    .order_by('-first_date')]

        return out_lst
        
    #get full invitation list
    def sorted_session_day_list_full(self):
        logger = logging.getLogger(__name__) 
    
        qs=self.user.ESDU.annotate(date=F('experiment_session_day__date'))\
                         .order_by('-date')

        out_str = [e.json_subjectInfo() for e in qs]      

        logger.info("get full invitation history")
        #logger.info(out_str)

        return out_str

    #get list of institutions this subject has been in
    def get_institution_list(self):
        l = institutions.objects.none()
        out_str=[]
        esdus=self.user.ESDU.filter(attended = True)

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
                logger.info("Bumped from last: User " + str(self.user.id) + ", date " +  str(ESDU_last.experiment_session_day.date))
                return True
            else:
                return False
        else:
            return False

    #return true if adding user to session creates recruitment violations in other future  accepted experiments
    def check_for_future_constraints(self,es):
        logger = logging.getLogger(__name__)
        logger.info("check for future constraints")

        qs_attending = self.sessions_upcoming(True,es.getFirstDate())

        #ignore cancel experiments
        qs_attending = qs_attending.filter(canceled=False)

        i_list = es.experiment.institution.values_list("id",flat=True)

        for s in qs_attending:
            user_list_valid = s.getValidUserList([{'id':self.user.id}],False,es.experiment.id,es.id,i_list,False)

            if not self.user in user_list_valid:
                logger.info("Invitation failed attended recruitment violation")             
                logger.info("User: " + str(self.user.id) + ", attending session: " + str(s.id) + " , violation experiment: " + str(es.experiment.id) )
                return True
                        
        return False

    #json version of model, small
    def json_min(self):
        return{
            "id":self.user.id,                        
            "first_name":self.user.first_name.capitalize(),   
            "last_name":self.user.last_name.capitalize(), 
            "email":self.user.email,
            "chapmanID":self.chapmanID,                 
        }

    #json version of model, full
    def json(self):
        return{
            "id":self.user.id,                        
            "first_name":self.user.first_name.capitalize(),   
            "last_name":self.user.last_name, 
            "email":self.user.email,
            "chapmanID":self.chapmanID, 
            "type":self.type.json(),  
            "gender":self.gender.json(),
            "email_confirmed":self.email_confirmed,  
            "blackballed":self.blackballed,         
        }

#delete associated user model when profile is deleted
@receiver(post_delete, sender=profile)
def post_delete_user(sender, instance, *args, **kwargs):
    if instance.user: # just in case user is not specified
        instance.user.delete()