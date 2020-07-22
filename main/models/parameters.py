from django.db import models
import logging
import traceback
from django.contrib.auth.models import User

#gloabal parameters for site
class parameters(models.Model):
    labManager = models.ForeignKey(User,on_delete=models.CASCADE,null=True) 
    subjectTimeZone = models.CharField(max_length = 1000,default = "US/Pacific")
    defaultShowUpFee = models.DecimalField(decimal_places=2, max_digits=5,default = 7)
    invitationText = models.CharField(max_length = 10000,default = "")
    invitationTextMultiDay = models.CharField(max_length = 10000,default = "")
    consentForm = models.CharField(max_length = 50000,default ="")
    
   

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