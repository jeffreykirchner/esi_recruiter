from django.db import models
import logging

from . import experiment_sessions
from django.contrib.auth.models import User

class experiment_session_messages(models.Model):
    experiment_session = models.ForeignKey(experiment_sessions,on_delete=models.CASCADE)
    users = models.ManyToManyField(User)

    subjectText = models.CharField(max_length = 1000,default = "")  
    messageText = models.CharField(max_length = 10000,default = "")  

    mailResultSentCount = models.IntegerField(default=0)
    mailResultErrorText = models.CharField(max_length = 10000,default = "")

    timestamp = models.DateTimeField(auto_now_add= True)
    updated = models.DateTimeField(auto_now= True)

    def __str__(self):
        return "ID: " + str(self.id)

    class Meta:                
        verbose_name = 'Experiment Session Messages'
        verbose_name_plural = 'Experiment Session Messages'
    
    def json(self):
        return{
            "id":self.id,
            "subjectText":self.subjectText,
            "messageText":self.messageText,
            "users":[u.profile.json_min() for u in self.users.all()],
            "date_raw":self.timestamp,
            "mailResultSentCount":self.mailResultSentCount,
            "mailResultErrorText":self.mailResultErrorText,
        }
