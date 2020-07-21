from django.db import models
import logging
import traceback
from datetime import datetime
from django.utils import timezone
from django.db.models import F

from django.contrib.auth.models import User

from . import experiment_sessions,locations,accounts,parameters
import main

from pytz import timezone


#one day of a session
class experiment_session_days(models.Model):
    experiment_session = models.ForeignKey(experiment_sessions,on_delete=models.CASCADE,related_name='ESD')
    location = models.ForeignKey(locations,on_delete=models.CASCADE)
    date = models.DateTimeField(default=datetime.now)
    length = models.IntegerField(default=60)    
    account = models.ForeignKey(accounts,on_delete=models.CASCADE)
    auto_reminder=models.SmallIntegerField (default=1)
    canceled=models.SmallIntegerField(default=0)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return "ID: " + str(self.id)

    class Meta:
        verbose_name = 'Experiment Session Days'
        verbose_name_plural = 'Experiment Session Days'

    def getListOfUserIDs(self):
        u_list=[]

        for u in self.experiment_session_day_users_set.all():
            u_list.append({'user':u.user,'confirmed':u.confirmed})

        #u_list.sort()

        return u_list

    #add user to session day
    def addUser(self,userID):
        esdu = main.models.experiment_session_day_users()

        esdu.experiment_session_day = self
        esdu.user = User.objects.get(id=userID)

        esdu.save()

    #sets up session day with defualt parameters
    def setup(self,es,u_list):
        self.experiment_session=es
        self.location = locations.objects.first()
        self.registration_cutoff = es.experiment.registration_cutoff_default
        self.actual_participants = es.experiment.actual_participants_default
        self.length=es.experiment.length_default
        self.account = es.experiment.account_default    
        self.date = datetime.now(timezone.utc)

        self.save()

        #add list of session users if multiday
        for u in u_list:
            esdu = main.models.experiment_session_day_users()
            esdu.user = u['user']
            esdu.confirmed = u['confirmed']
            esdu.experiment_session_day = self
            esdu.save()

    #check if this session day can be deleted
    def allowDelete(self):

        ESDU = self.experiment_session_day_users_set.all()    

        for u in ESDU:
            if not u.allowDelete():
                return False

        return True  

    def getDateString(self):
        p = parameters.parameters.objects.get(id=1)
        return  self.date.astimezone(timezone(p.subjectTimeZone)).strftime("%#m/%#d/%Y %#I:%M %p") + " " + p.subjectTimeZone


    def json_min(self):
        return{
            "id":self.id,
            "date":self.date,
        }

    def json(self):
        u_list_c = self.experiment_session_day_users_set.filter(confirmed=True).order_by("user__last_name").prefetch_related('user') 
        u_list_u= self.experiment_session_day_users_set.filter(confirmed=False).order_by("user__last_name").prefetch_related('user')

        return{
            "id":self.id,
            "location":self.location.id,
            "date":self.getDateString(),
            "date_raw":self.date,
            "length":self.length,
            "account":self.account.id,
            "auto_reminder":self.auto_reminder,
            "canceled":str(self.canceled),
            "experiment_session_days_user" : [i.json_min() for i in u_list_c],
            "experiment_session_days_user_unconfirmed" : [i.json_min() for i in u_list_u],
            "confirmedCount": self.experiment_session_day_users_set.filter(confirmed=True).count(),
            "unConfirmedCount": self.experiment_session_day_users_set.filter(confirmed=False).count(),          
        }
        
    def json_unconfirmed(self):
        return{
            "experiment_session_days_user_unconfirmed" : [i.json_min() for i in self.experiment_session_day_users_set.all() \
                                                                                    .annotate(last_name = F('user__last_name')) \
                                                                                    .order_by("last_name") \
                                                                                    .filter(confirmed=False)],
            "unConfirmedCount": self.experiment_session_day_users_set.all().filter(confirmed=False).count(),
        }