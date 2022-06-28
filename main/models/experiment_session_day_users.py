from datetime import datetime

import uuid
import pytz

from django.db import models
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder

from main.models import experiment_session_days

import main

#user results from a session day
class experiment_session_day_users(models.Model):        
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ESDU')    
    experiment_session_day = models.ForeignKey(experiment_session_days, on_delete=models.CASCADE, null = True, related_name='ESDU_b')                                                                                               
    addedByUser = models.ForeignKey(User,on_delete=models.CASCADE, null=True)              #staff user who added to session

    attended = models.BooleanField(default=False)                                    #true once a subject has been marked as attended
    bumped = models.BooleanField(default=False)                                      #true if user has been bumped from session 
    confirmed = models.BooleanField(default=False)                                   #true once user has confirmed desire to attend
    confirmationHash = models.UUIDField(default=uuid.uuid4, editable=False)          #code used for direct confirmation (not in use)   
    show_up_fee = models.DecimalField(max_digits=10, decimal_places=6, default = 0)  #amount subject earned for just for coming
    earnings = models.DecimalField(max_digits=10, decimal_places=6, default = 0)     #amount subject earned in experiment  
    multi_day_legacy = models.BooleanField(default=False, null=True)                 #needed to transition from old to new multiday model
    manuallyAdded = models.BooleanField(default=False)                               #true if subject was manually added to a session

    paypal_response = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)   #response from paypal after payment

    timestamp = models.DateTimeField(auto_now_add=True)
    updated= models.DateTimeField(auto_now=True)

    def __str__(self):
        return "ID:" + str(self.id)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'experiment_session_day'], name='unique_ESDU')
        ]        
        verbose_name = 'Experiment Session Day Users'
        verbose_name_plural = 'Experiment Session Day Users'
    
    #check if session day user can be deleted
    def allowConfirm(self):
        if self.attended or self.bumped:
            return False
        else:
            return True 
    
    # check if session user can be deleted
    def allowDelete(self):       

        esdu=main.models.experiment_session_day_users.objects.filter(user__id = self.user.id,
                                                         experiment_session_day__experiment_session__id = self.experiment_session_day.experiment_session.id)

        for i in esdu:
            if i.attended or i.bumped:
                return False 

        return True 

    #check if subject is violation of attending experiment twice
    def getAlreadyAttended(self):

        #multiple participations are allowed
        if self.experiment_session_day.experiment_session.recruitment_params.allow_multiple_participations:
            return False

        experiment_id = self.experiment_session_day.experiment_session.experiment.id

        esdu_list = main.models.experiment_session_day_users.objects\
                               .filter(experiment_session_day__experiment_session__experiment__id=experiment_id)\
                               .filter(user__id=self.user.id)\
                               .filter(attended=True)\
                               .exclude(experiment_session_day__experiment_session__id=self.experiment_session_day.experiment_session.id)

        if esdu_list:
            return True
        
        return False

    def get_total_payout(self):
        '''
        return total earnings
        '''
        total_payout = 0

        if self.attended:
            total_payout = self.earnings + self.show_up_fee
        elif self.bumped:
            total_payout = self.show_up_fee
        else:
            total_payout = 0
        
        return round(total_payout, 2)

    #get json info on session user
    def json_subjectInfo(self):
        
        return{
            "id":self.id,
            "title":mark_safe(self.experiment_session_day.experiment_session.experiment.title),
            "canceled": self.experiment_session_day.experiment_session.canceled,
            "session_id":self.experiment_session_day.experiment_session.id,
            "date":self.experiment_session_day.date,
            "enable_time":self.experiment_session_day.enable_time,
            "attended":self.attended,
            "bumped":self.bumped,
            "earnings": self.earnings,
            "show_up_fee":self.show_up_fee,
            "total_earnings":self.get_total_payout(),
            "confirmed":self.confirmed,
            "multiDay":self.getMultiDay(),
            "alreadyAttending":self.getAlreadyAttended(),
            "consent_form":self.experiment_session_day.experiment_session.consent_form.json() if self.experiment_session_day.experiment_session.consent_form else None,        
            "noShow":True if self.confirmed and
                             not self.attended and
                             not self.bumped and
                             self.experiment_session_day.complete and
                             self.experiment_session_day.experiment_session.canceled == False and
                             datetime.now(pytz.UTC) > self.experiment_session_day.date_end else False,
        }
    
    #get multiday status of session
    def getMultiDay(self):
        return True if self.experiment_session_day.experiment_session.ESD.count() > 1 else False
    
    #return a list of values for a paypal csv mass pay file
    def csv_payPal(self):

        # totalEarnings = 0

        # if self.attended:
        #     totalEarnings = self.earnings + self.show_up_fee
        # else:
        #     totalEarnings = self.show_up_fee

        s=[]

        s.append(self.user.email)
        s.append(self.get_total_payout())
        s.append("USD")
        s.append(self.user.profile.studentID)
        s.append("Session Day ID: " + str(self.experiment_session_day.id))

        return s
    
   #return a list of values for a earnings csv file
    def csv_earnings(self):

        s=[]

        s.append(self.user.last_name)
        s.append(self.user.first_name)
        s.append(self.user.email)
        s.append(self.user.profile.studentID)
        s.append(self.earnings)
        s.append(self.show_up_fee)

        s.append(str(self.experiment_session_day.id))

        return s

    def json_runInfo(self):

        profile_consent_form = self.user.profile.profile_consent_forms_a.filter(consent_form=self.experiment_session_day.experiment_session.consent_form).first()

        return{"id":self.id,            
                "attended":self.attended,
                "bumped":self.bumped,
                "show_up_fee":f'{self.show_up_fee:.2f}',
                "earnings":f'{self.earnings:.2f}',
                "payout":  f'{self.get_total_payout():.2f}',
                "waiting":False,
                "show":True,
                "profile_consent_form":profile_consent_form.json() if profile_consent_form else None,
                "paypal_response":self.paypal_response,
                "user":{"id" : self.user.id,
                        "first_name":self.user.first_name.capitalize(),   
                        "last_name":self.user.last_name.capitalize(),
                        "studentID":self.user.profile.studentID,
                        "bumpedFromLast":self.user.profile.bumped_from_last_session(self.id)},                 
                }

    def json_min(self):
        return{
            "id":self.id,            
            "confirmed":self.bumped,
            "user":self.user.profile.json_min(),  
            "allowDelete" : self.allowDelete(),
            "allowConfirm" : self.allowConfirm(),
            "alreadyAttending":self.getAlreadyAttended(),       
        }