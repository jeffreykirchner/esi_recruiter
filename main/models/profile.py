from django.db import models
import logging
import traceback
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

from . import *

#user profile, extending the user model
class profile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    type =  models.ForeignKey(accountTypes,on_delete=models.CASCADE,default=2)             #subject or staff
    school = models.ForeignKey(schools,on_delete=models.CASCADE,default=1)                 #Chapman University ETC
    major = models.ForeignKey(majors,on_delete=models.CASCADE,default=1)                   #Economics ETC
    gender = models.ForeignKey(genders,on_delete=models.CASCADE,default=1)

    chapmanID = models.CharField(max_length = 100,default="00000000")    
    emailConfirmed =  models.CharField(max_length = 100,default="no")    
    blackballed = models.BooleanField(default=False)
    gradStudent = models.BooleanField(default=False)
    phone = models.CharField(max_length = 100,default="")
    studentWorker = models.BooleanField(default=False)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return "Name: %s %s, Chapman ID: %s" % (self.user.first_name, self.user.last_name,self.chapmanID)

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