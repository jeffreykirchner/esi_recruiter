from django.db import models
import logging
import traceback
from datetime import datetime

from . import experiment_sessions,locations,accounts

#one day of a session
class experiment_session_days(models.Model):
    experiment_session = models.ForeignKey(experiment_sessions,on_delete=models.CASCADE)
    location = models.ForeignKey(locations,on_delete=models.CASCADE)
    registration_cutoff = models.IntegerField(default=1)
    actual_participants = models.IntegerField(default=1)
    date = models.DateTimeField(default=datetime.now)
    length = models.IntegerField(default=60)    
    account = models.ForeignKey(accounts,on_delete=models.CASCADE)
    auto_reminder=models.SmallIntegerField (default=1)
    canceled=models.SmallIntegerField(default=0)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return "ID: " + self.id

    class Meta:
        verbose_name = 'Experiment Session Days'
        verbose_name_plural = 'Experiment Session Days'

    def setup(self,es):
        self.experiment_session=es
        self.location = locations.objects.first()
        self.registration_cutoff = es.experiment.registration_cutoff_default
        self.actual_participants = es.experiment.actual_participants_default
        self.length=es.experiment.length_default
        self.account = es.experiment.account_default      

    def json_min(self):
        return{
            "id":self.id,
            "date":self.date,
        }

    def json(self):
        return{
            "id":self.id,
            "location":self.location.id,
            "registration_cutoff":self.registration_cutoff,
            "actual_participants":self.actual_participants,
            "date":self.date.strftime("%#m/%#d/%Y %#I:%M %p"),
            "date_raw":self.date,
            "length":self.length,
            "account":self.account.id,
            "auto_reminder":self.auto_reminder,
            "canceled":str(self.canceled),
            "experiment_session_days_user" : [i.json_min() for i in self.experiment_session_day_users_set.all().filter(confirmed=True)],
            "confirmedCount": self.experiment_session_day_users_set.all().filter(confirmed=True).count(),
            "unConfirmedCount": self.experiment_session_day_users_set.all().filter(confirmed=False).count(),          
        }

    def json_unconfirmed(self):
        return{
            "experiment_session_days_user_unconfirmed" : [i.json_min() for i in self.experiment_session_day_users_set.all().filter(confirmed=False)],
            "unConfirmedCount": self.experiment_session_day_users_set.all().filter(confirmed=False).count(),
        }