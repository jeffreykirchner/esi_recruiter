'''
site wide parameters
'''
from tinymce.models import HTMLField

from django.db import models
from django.contrib.auth.models import User

class Parameters(models.Model):
    '''
    site wide parameters
    '''
    labManager = models.ForeignKey(User, on_delete=models.CASCADE, null=True)             #primary contact for subjects
    subjectTimeZone = models.CharField(max_length=1000, default="US/Pacific")             #time zone the lab is in
    defaultShowUpFee = models.DecimalField(decimal_places=2, max_digits=5, default=7)     #money paid to subjects for coming regardless of performance
    maxAnnualEarnings = models.DecimalField(decimal_places=2, max_digits=5, default=600)  #max money that can be paid to a subject per year  
    siteURL = models.CharField(max_length=200, default="https://www.google.com/")         #site URL used for display in emails
    testEmailAccount = models.CharField(max_length=1000, default="")                      #email account used for debug mode emails
    max_invitation_block_size = models.IntegerField(default=100)                          #max number of subjects that can be invited in one invitation block
    noShowCutoff = models.IntegerField(default=3)                                         #if subject hits count in window they will not be invited
    noShowCutoffWindow = models.IntegerField(default=90)                                  #trailing window in days with which no shows are measured
    international_tax_rate = models.DecimalField(decimal_places=2, max_digits=5, default=0.3)  #tax rate for international students

    paypal_email_subject = models.CharField(max_length=200, default="You have a payment from <your_org>.")     #subject of paypal payment emails
    paypal_email_body = models.CharField(max_length=200, default="thanks for your participation!")             #body of paypal payment email

    invitationTextSubject = models.CharField(max_length=1000, default="")                 #email subject text for the single day invitation
        
    cancelationTextSubject = models.CharField(max_length = 1000, default="")              #email subject text when an experiment is canceled
    cancelationText = HTMLField(default="")                                               #email text when an experiment is canceled
    
    reminderTextSubject = models.CharField(max_length = 1000,default = "")                 #email subject text to remind subjects 24 hours before start
    reminderText = HTMLField(default = "")                                                 #email text to remind subjects 24 hours before start

    deactivationTextSubject = models.CharField(max_length = 1000,default = "")             #email subject text to  subject when account is deactivated
    deactivationText = HTMLField(default = "")                                             #email text to  subject when account is deactivated

    passwordResetTextSubject = models.CharField(max_length = 1000,default = "")             #email subject text when password reset
    passwordResetText = HTMLField(default = "")                                             #email text sent when password reset

    emailVerificationTextSubject = models.CharField(max_length = 1000,default = "")         #email subject sent to user to verify their email address
    emailVerificationResetText = HTMLField(default = "")                                    #email text sent to user to verify their email address

    timestamp = models.DateTimeField(auto_now_add= True)
    updated = models.DateTimeField(auto_now= True)

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
            "reminderText":self.reminderText,
            "noShowCutoff":str(self.noShowCutoff),
            "noShowCutoffWindow":(self.noShowCutoffWindow),
        }