import logging
import traceback

from django.db import models
from django.contrib.auth.models import User

from main.models import profile
from main.models import ConsentForm

class ProfileConsentForm(models.Model):
    '''
    consent form agreed to by subject
    '''
    my_profile = models.ForeignKey(profile, on_delete=models.CASCADE, related_name="profile_consent_forms_a")               #profile that note is attached to
    consent_form = models.ForeignKey(ConsentForm, on_delete=models.CASCADE, related_name="profile_consent_forms_b")         #consent form

    timestamp = models.DateTimeField(auto_now_add=True)
    updated= models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'User: {self.my_profile}, Form: {self.consent_form}'

    class Meta:
        verbose_name = 'Profile Consent Form'
        verbose_name_plural = 'Profile Consent Forms'

        constraints = [
            models.UniqueConstraint(fields=['my_profile', 'consent_form'], name='unique_profile_consent_form')
        ]  
    
    def json(self):
        return {
            "id" : self.id,
        }
        

