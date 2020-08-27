from django.db import models
import logging
import traceback
from . import profile
from django.contrib.auth.models import User

#a note or comment made abbout a user
class profile_note(models.Model):
    my_profile = models.ForeignKey(profile,on_delete=models.CASCADE)               #profile that note is attached to
    noteMaker = models.ForeignKey(User,on_delete=models.CASCADE)                   #user that made the note

    text = models.CharField(max_length = 1000)                                      #text of the note

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.note

    class Meta:
        verbose_name = 'Profile Note'
        verbose_name_plural = 'Profile Notes'
    
    def json(self):
        return {
            "id" : self.id,
            "text" : self.text,
            "noteMaker" : {"id" : self.noteMaker.id,
                           "first_name" : self.noteMaker.first_name,
                           "last_name" : self.noteMaker.last_name,
                            },
            "date" : self.timestamp,
        }
        

