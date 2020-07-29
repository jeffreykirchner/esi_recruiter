from django.db import models
import logging
import traceback
from django.contrib.auth.models import User

#gloabal parameters for site
class parameters(models.Model):
    labManager = models.ForeignKey(User,on_delete=models.CASCADE,null=True)                #primary contact for subjects
    subjectTimeZone = models.CharField(max_length = 1000,default = "US/Pacific")           #time zone the lab is in
    defaultShowUpFee = models.DecimalField(decimal_places=2, max_digits=5,default = 7)     #money paid to subjects for coming regardless of performance
    
    invitationTextSubject = models.CharField(max_length = 1000,default = "")               #email subject text for the single day invitation
    invitationText = models.CharField(max_length = 10000,default = "")                     #email text for the single day invitation
    
    invitationTextMultiDaySubject = models.CharField(max_length = 1000,default = "")       #email subject text for a multiday experiment
    invitationTextMultiDay = models.CharField(max_length = 10000,default = "")             #email text for a multiday experiment
    
    cancelationTextSubject = models.CharField(max_length = 1000,default = "")              #email subject text when an experiment is canceled
    cancelationText = models.CharField(max_length = 10000,default = "")                    #email text when an experiment is canceled
    
    consentForm = models.CharField(max_length = 50000,default ="")                         #consent for subject must agree to before participation 

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return "Site Parameters"

    class Meta:
        verbose_name = 'Parameters'
        verbose_name_plural = 'Parameters'
    
    def json(self):
        return{
            "labManager":self.labManager.last_name + ", " + self.labManager.first_name,
            "subjectTimeZone":self.subjectTimeZone,
            "defaultShowUpFee":str(self.defaultShowUpFee),
            "invitationText":self.invitationText,
            "invitationTextMultiDay":self.invitationTextMultiDay,
            "consentForm":self.consentForm,
        }