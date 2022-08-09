
import pytz

from django.db import models
from django.core.serializers.json import DjangoJSONEncoder

from main.models import profile
from main.models import ConsentForm
from main.models import parameters

class ProfileConsentForm(models.Model):
    '''
    consent form agreed to by subject
    '''
    my_profile = models.ForeignKey(profile, on_delete=models.CASCADE, related_name="profile_consent_forms_a")               #profile that note is attached to
    consent_form = models.ForeignKey(ConsentForm, on_delete=models.CASCADE, related_name="profile_consent_forms_b")         #consent form

    signature_points = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)                #points used to draw signature
    singnature_resolution = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)           #points used to draw signature

    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'User: {self.my_profile}, Form: {self.consent_form}'

    class Meta:
        verbose_name = 'Profile Consent Form'
        verbose_name_plural = 'Profile Consent Forms'

        constraints = [
            models.UniqueConstraint(fields=['my_profile', 'consent_form'], name='unique_profile_consent_form')
        ]  

        ordering = ['my_profile__user__last_name', 'my_profile__user__first_name']
    
    def get_date_string_tz_offset(self):
        '''
        return a date string converted to the lab's time zone
        '''
        p = parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)
        return  self.updated.astimezone(tz).strftime("%-m/%-d/%Y")
    
    def json(self):
        return {
            "id" : self.id,
            "signature_points" : self.signature_points,
            "singnature_resolution" : self.singnature_resolution,
            "date_string" : self.get_date_string_tz_offset(),
        }

    def json_report(self):
        return {
            "id" : self.id,
            "name" : f"{self.my_profile.user.last_name}, {self.my_profile.user.first_name}",
            "signature_points" : self.signature_points,
            "singnature_resolution" : self.singnature_resolution,
            "date_string" : self.get_date_string_tz_offset(),
        }
        

