from django.db import models
import logging
import traceback
from django.contrib.auth.models import User

from . import *

#user profile, extending the user model
class profile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    chapmanID = models.CharField(max_length = 100,default="00000000")
    type =  models.ForeignKey(accountTypes,on_delete=models.CASCADE,default=2)             #subject or staff
    school = models.ForeignKey(schools,on_delete=models.CASCADE,default=1)                 #Chapman University ETC
    major = models.ForeignKey(majors,on_delete=models.CASCADE,default=1)                   #Economics ETC
    #type = models.CharField(max_length=10, default="")
    emailConfirmed =  models.CharField(max_length = 100,default="no")
    gender = models.ForeignKey(genders,on_delete=models.CASCADE,default=1)
    blackballed = models.BooleanField(default=False)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

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