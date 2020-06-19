from django.db import models
import logging
import traceback
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db.models import F,Q

from main.models import *

from django.dispatch import receiver
from django.db.models.signals import post_delete

import logging

#user profile, extending the user model
class profile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    type =  models.ForeignKey(accountTypes,on_delete=models.CASCADE,default=2)             #subject or staff
    school = models.ForeignKey(schools,on_delete=models.CASCADE,default=1)                 #Chapman University ETC
    major = models.ForeignKey(majors,on_delete=models.CASCADE,default=1)                   #Economics ETC
    gender = models.ForeignKey(genders,on_delete=models.CASCADE,default=1)
    subjectType = models.ForeignKey(subject_types,on_delete=models.CASCADE,default=1)      #Undergrad, grad, non student

    chapmanID = models.CharField(max_length = 100,default="00000000")    
    emailConfirmed =  models.CharField(max_length = 100,default="no")    
    blackballed = models.BooleanField(default=False)
    phone = models.CharField(max_length = 100,default="")
    studentWorker = models.BooleanField(default=False)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return "%s, %s | Chapman ID: %s" % (self.user.last_name,self.user.first_name,self.chapmanID)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'


    def sorted_session_day_list_earningsOnly(self):
        logger = logging.getLogger(__name__) 

        qs=self.user.ESDU.all().filter(Q(attended=True)|Q(bumped=True)) \
                                 .annotate(date=F('experiment_session_day__date')).order_by('-date')
                               
        return  [e.json_subjectInfo() for e in qs]

    def json_min(self):
        return{
            "id":self.user.id,                        
            "first_name":self.user.first_name,   
            "last_name":self.user.last_name, 
            "email":self.user.email,
            "chapmanID":self.chapmanID,                 
        }

    def json(self):
        return{
            "id":self.user.id,                        
            "first_name":self.user.first_name,   
            "last_name":self.user.last_name, 
            "email":self.user.email,
            "chapmanID":self.chapmanID, 
            "type":self.type.json(),  
            "gender":self.gender.json(),
            "emailConfirmed":self.emailConfirmed,  
            "blackballed":self.blackballed,         
        }

#delete associated user model
@receiver(post_delete, sender=profile)
def post_delete_user(sender, instance, *args, **kwargs):
    if instance.user: # just in case user is not specified
        instance.user.delete()