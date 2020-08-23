from django.db import models
import logging
import traceback
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db.models import F,Q

from main.models import *
from main.models import institutions
from . import emailFilters

import main

from django.dispatch import receiver
from django.db.models.signals import post_delete

from datetime import date
from datetime import datetime, timedelta,timezone

import logging

#user profile, extending the user model
class profile(models.Model):

    user = models.OneToOneField(User,verbose_name="User", on_delete=models.CASCADE)
    type =  models.ForeignKey(accountTypes,verbose_name="Account Type",on_delete=models.CASCADE,default=2)            #subject or staff
    school = models.ForeignKey(schools,verbose_name="School",on_delete=models.CASCADE,default=1)                      #Chapman University ETC
    major = models.ForeignKey(majors,verbose_name="Major",on_delete=models.CASCADE,default=1)                         #Economics ETC
    gender = models.ForeignKey(genders,verbose_name="Gender",on_delete=models.CASCADE,default=1)
    subjectType = models.ForeignKey(subject_types,verbose_name="Subject Type",on_delete=models.CASCADE,default=1)      #Undergrad, grad, non student
    emailFilter = models.ForeignKey(emailFilters, verbose_name="Email Filter",on_delete=models.CASCADE,null=True)     #email filters that apply to this user

    chapmanID = models.CharField(verbose_name="ID Number",max_length = 100,default="00000000")    
    emailConfirmed =  models.CharField(verbose_name="Email Confirmed",max_length = 100,default="no")    
    blackballed = models.BooleanField(verbose_name="Blackballed",default=False)
    phone = models.CharField(verbose_name="Phone Number",max_length = 100,default="")
    studentWorker = models.BooleanField(verbose_name="Student Woker",default=False)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return "%s, %s | Chapman ID: %s" % (self.user.last_name,self.user.first_name,self.chapmanID)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def setupEmailFilter(self):
        logger = logging.getLogger(__name__) 
        logger.info("set email filter")
        
        self.emailFilter = None
        self.save()

        if not "@" in self.user.email:
            return 0

        email_split = self.user.email.split("@")

        #logger.info(email_split)

        #domain__regex = r'.+@' + email_regx
        ef = emailFilters.objects.filter(domain = email_split[1]).first()

        if ef:
            self.emailFilter = ef
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
        logger.info(out_str)

        return out_str
    
    #get a list of upcoming experiments that subject has confirmed for
    def sorted_session_day_list_upcoming(self):
        logger = logging.getLogger(__name__) 

        t = date.today()

        qs=self.user.ESDU.annotate(date=F('experiment_session_day__date'))\
                         .annotate(session_id=F('experiment_session_day__experiment_session__id'))\
                         .filter(confirmed=True,date__gte = t)\
                         .order_by('-date')

        out_str = [e.json_subjectInfo() for e in qs]
      

        logger.info("get upcoming session day list")
        logger.info(out_str)

        return out_str
    
    #get full invitation list
    def sorted_session_day_list_full(self):
        logger = logging.getLogger(__name__) 
    
        qs=self.user.ESDU.annotate(date=F('experiment_session_day__date'))\
                         .order_by('-date')

        out_str = [e.json_subjectInfo() for e in qs]      

        logger.info("get full invitation history")
        logger.info(out_str)

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

    #return true if subject was bumped from last session they attended
    def bumped_from_last_session(self,excludeESDU):
        logger = logging.getLogger(__name__)
        logger.info("Get bumped from last session")

        d = datetime.now(timezone.utc)
        ESDU_last = self.user.ESDU.exclude(id = excludeESDU).filter(confirmed = True,experiment_session_day__date__lt = d).order_by("-experiment_session_day__date").first()

        logger.info(ESDU_last.experiment_session_day.date)

        if ESDU_last.bumped:
            return True
        else:
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
            "emailConfirmed":self.emailConfirmed,  
            "blackballed":self.blackballed,         
        }

#delete associated user model when profile is deleted
@receiver(post_delete, sender=profile)
def post_delete_user(sender, instance, *args, **kwargs):
    if instance.user: # just in case user is not specified
        instance.user.delete()