from django.db import models
import logging
import main

from . import experiment_sessions,recruitment_parameters
from django.contrib.auth.models import User

from django.dispatch import receiver
from django.db.models.signals import post_delete

class experiment_session_invitations(models.Model):
    experiment_session = models.ForeignKey(experiment_sessions, on_delete=models.CASCADE, related_name='experiment_session_invitations')
    recruitment_params = models.ForeignKey(recruitment_parameters, on_delete=models.CASCADE, null=True)

    users = models.ManyToManyField(User, related_name='experiment_session_invitation_users')

    subjectText = models.CharField(max_length=1000, default="")  
    messageText = models.CharField(max_length=10000, default="")  

    mailResultSentCount =  models.IntegerField(default=0)
    mailResultErrorText = models.CharField(max_length=10000, default="")

    timestamp = models.DateTimeField(auto_now_add= True)
    updated = models.DateTimeField(auto_now= True)   

    def __str__(self):
        return "ID: " + str(self.id)

    class Meta:                
        verbose_name = 'Experiment Session Invitations'
        verbose_name_plural = 'Experiment Session Invitations'    
    
    
    def json(self):
        return{
            "id":self.id,
            "subjectText":self.subjectText,
            "messageText":self.messageText,
            "users":[u.profile.json_min() for u in self.users.all()],
            "date_raw":self.timestamp,
            "mailResultSentCount":self.mailResultSentCount,
            "mailResultErrorText":self.mailResultErrorText,
            "recruitment_params":self.recruitment_params.json_displayString(),
        }

#delete recruitment parameters when deleted
@receiver(post_delete, sender=experiment_session_invitations)
def post_delete_recruitment_params(sender, instance, *args, **kwargs):
    if instance.recruitment_params: # just in case user is not specified
        instance.recruitment_params.delete()
