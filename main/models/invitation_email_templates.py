from django.db import models
import logging
import traceback
from . import profile,Traits,parameters
from django.contrib.auth.models import User

from datetime import datetime, timedelta,timezone
import pytz

#a user trait
class Invitation_email_templates(models.Model):
    name = models.CharField(verbose_name="Subject Text", max_length = 1000,default = "")           #template name
    subject_text = models.CharField(verbose_name="Subject Text", max_length = 1000,default = "")   #email subject
    body_text = models.CharField(verbose_name="Body Text", max_length = 10000,default = "")        #email text

    enabled = models.BooleanField(default=True)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'{self.subject_text}'

    class Meta:
        
        verbose_name = 'Invitation Email Template'
        verbose_name_plural = 'Invitation Email Templates'
    
    def json(self):
        return {
            "id" : self.id,
            "name":self.name,
            "subject_text" : self.subject_text,
            "body_text" : self.body_text,
            "enabled" : self.enabled,
        }
        

