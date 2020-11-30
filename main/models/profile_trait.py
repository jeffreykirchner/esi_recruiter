from django.db import models
import logging
import traceback
from . import profile,traits,parameters
from django.contrib.auth.models import User

from datetime import datetime, timedelta,timezone
import pytz

#a user trait
class profile_trait(models.Model):
    my_profile = models.ForeignKey(profile,on_delete=models.CASCADE,related_name="profile_traits")     #profile that note is attached to
    trait = models.ForeignKey(traits,on_delete=models.CASCADE)                                         #user that made the note
    value = models.DecimalField(decimal_places=2, max_digits=10,default = 0)                           #score user received on trait

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'trait {self.trait.name} score {self.score}'

    class Meta:
        verbose_name = 'Profile Trait'
        verbose_name_plural = 'Profile Traits'

    def getDateStringTZOffset(self):
        p = parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)
        return  self.updated.astimezone(tz).strftime("%#m/%#d/%Y %#I:%M %p")
    
    def json(self):
        return {
            "id" : self.id,
            "name" : self.trait.name,
            "value" : f'{self.value:0.2f}',
            "date" : self.getDateStringTZOffset(),
        }
        

