from django.db import models
import logging
import traceback
from django.contrib.auth.models import User

#gloabal parameters for site
class parameters(models.Model):
    labManager = models.ForeignKey(User,on_delete=models.CASCADE,null=True) 
    invitationText = models.CharField(max_length = 10000)
    consentForm = models.CharField(max_length = 50000)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return "Site Parameters"

    class Meta:
        verbose_name = 'Parameters'
        verbose_name_plural = 'Parameters'
    
    def json(self):
        return{
            "id":self.id,
        }