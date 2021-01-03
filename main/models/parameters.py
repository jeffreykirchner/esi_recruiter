from django.db import models
import logging
import traceback
from django.contrib.auth.models import User

#gloabal parameters for site
class parameters(models.Model):
    labManager = models.ForeignKey(User,on_delete=models.CASCADE,null=True)                #primary contact for subjects
    subjectTimeZone = models.CharField(max_length = 1000,default = "US/Pacific")           #time zone the lab is in
    defaultShowUpFee = models.DecimalField(decimal_places=2, max_digits=5,default = 7)     #money paid to subjects for coming regardless of performance
    maxAnnualEarnings = models.DecimalField(decimal_places=2, max_digits=5,default = 600)  #max money that can be paid to a subject per year  
    siteURL = models.CharField(max_length = 200,default = "https://www.google.com/")       #site URL used for display in emails

    noShowCutoff = models.IntegerField(default = 3)                                         #if subject hits count in window they will not be invited
    noShowCutoffWindow = models.IntegerField(default = 90)                                  #trailing window in days with which no shows are measured

    invitationTextSubject = models.CharField(max_length = 1000,default = "")               #email subject text for the single day invitation
    invitationText = models.CharField(max_length = 10000,default = "")                     #email text for the single day invitation
    
    invitationTextMultiDaySubject = models.CharField(max_length = 1000,default = "")       #email subject text for a multiday experiment
    invitationTextMultiDay = models.CharField(max_length = 10000,default = "")             #email text for a multiday experiment
    
    cancelationTextSubject = models.CharField(max_length = 1000,default = "")              #email subject text when an experiment is canceled
    cancelationText = models.CharField(max_length = 10000,default = "")                    #email text when an experiment is canceled
    
    reminderTextSubject = models.CharField(max_length = 1000,default = "")                 #email subject text to remind subjects 24 hours before start
    reminderText = models.CharField(max_length = 10000,default = "")                       #email text to remind subjects 24 hours before start

    deactivationTextSubject = models.CharField(max_length = 1000,default = "")             #email subject text to  subject when account is deactivated
    deactivationText = models.CharField(max_length = 10000,default = "")                   #email text to  subject when account is deactivated

    passwordResetTextSubject = models.CharField(max_length = 1000,default = "")             #email subject text when password reset
    passwordResetText = models.CharField(max_length = 10000,default = "")                   #email text sent when password reset

    consentForm = models.CharField(max_length = 50000, default ="")                        #consent for subject must agree to before participation 

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
            "reminderText":self.reminderText,
            "consentForm":self.consentForm,
            "noShowCutoff":str(self.noShowCutoff),
            "noShowCutoffWindow":(self.noShowCutoffWindow),
        }