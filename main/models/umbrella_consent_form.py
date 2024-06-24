
import pytz

from django.db import models
from django.core.serializers.json import DjangoJSONEncoder

from main.models import profile
from main.models import ConsentForm
from main.models import Parameters

class UmbrellaConsentForm(models.Model):
    '''
    consent form that must be agreed to by all subjects before continuing
    '''   
    consent_form = models.ForeignKey(ConsentForm, on_delete=models.CASCADE, related_name="umbrella_consent_forms")                #consent form

    display_name = models.CharField(verbose_name="Displayed name to subjects", max_length = 100, default="", unique=True)         #name of consent form displayed to subjects
    active = models.BooleanField(verbose_name="Active", default=False)                                                            #if active subjects must complete consent form before continuing   
 
    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.display_name}'

    class Meta:
        verbose_name = 'Umbrella Consent Form'
        verbose_name_plural = 'Umbrella Consent Forms'

    
    def get_date_string_tz_offset(self):
        '''
        return a date string converted to the lab's time zone
        '''
        p = Parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)
        return  self.updated.astimezone(tz).strftime("%-m/%-d/%Y")
    
    def json(self):
        return {
            "id" : self.id,
            "display_name" : self.display_name,
            "active" : self.active,           
            "consent_form" : self.consent_form.id,
        }
        

