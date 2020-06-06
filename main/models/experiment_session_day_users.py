from django.db import models
import logging
import traceback
import uuid

from . import experiment_session_days,experiment_sessions

from django.contrib.auth.models import User

#user results from a session day
class experiment_session_day_users(models.Model):        
    user = models.ForeignKey(User,on_delete=models.CASCADE)    
    experiment_session_day = models.ForeignKey(experiment_session_days,on_delete=models.CASCADE,null = True)                                                                                               
    experiment_session_legacy = models.ForeignKey(experiment_sessions,on_delete=models.CASCADE,null=True)

    attended=models.BooleanField(default=False)
    bumped=models.BooleanField(default=False)
    confirmed=models.BooleanField(default=False)   
    confirmationHash=models.UUIDField(default=uuid.uuid4,editable=False)
    show_up_fee = models.DecimalField(max_digits=10, decimal_places=6)
    earnings = models.DecimalField(max_digits=10, decimal_places=6)
    multi_day_legacy = models.BooleanField(default=False,null=True)   #needed to transition from old to new multiday model

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)
    
    def json_min(self):
        return{
            "id":self.id,            
            "confirmed":self.bumped,
            "user":self.user.profile.json_min(),         
        }