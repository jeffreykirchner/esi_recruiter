import pytz

from django.db import models
from django.db.models.functions import Lower

from main.models import profile
from main.models import Traits
from main.models import parameters

#a user trait
class profile_trait(models.Model):
    my_profile = models.ForeignKey(profile, on_delete=models.CASCADE, related_name="profile_traits")     #profile that note is attached to
    trait = models.ForeignKey(Traits, on_delete=models.CASCADE)                                         #user that made the note
    value = models.DecimalField(decimal_places=2, max_digits=10, default = 0)                           #score user received on trait

    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.my_profile.user.last_name}, {self.my_profile.user.first_name} : {self.trait.name} | {self.value}'

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['my_profile', 'trait'], name='unique_PT')
        ]
        verbose_name = 'Profile Trait'
        verbose_name_plural = 'Profile Traits'
        ordering = [Lower('trait__name')]

    def getDateStringTZOffset(self):
        p = parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)
        return  self.updated.astimezone(tz).strftime("%-m/%d/%Y, %-I:%M %p")
    
    def json(self):
        return {
            "id" : self.id,
            "name" : self.trait.name,
            "value" : f'{self.value:0.2f}',
            "description" : self.trait.description,
            "date" : self.getDateStringTZOffset(),
        }
        

