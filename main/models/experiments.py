'''
experiment model
'''
from datetime import datetime

import logging
import pytz

from tinymce.models import HTMLField

from django.db import models
from django.utils.safestring import mark_safe
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.contrib.auth.models import User
from django.db.models import Max

from main.models import schools
from main.models import Accounts
from main.models import Institutions 
from main.models import recruitment_parameters
from main.models import Parameters
from main.models import ConsentForm

import main

class Experiments(models.Model):    
    '''
    experiment model
    '''

    school = models.ForeignKey(schools, on_delete=models.CASCADE)
    account_default = models.ForeignKey(Accounts, on_delete=models.CASCADE)
    recruitment_params_default = models.ForeignKey(recruitment_parameters, on_delete=models.CASCADE, null=True)  #default parameters used for new sessions
    consent_form_default = models.ForeignKey(ConsentForm, on_delete=models.CASCADE, null=True, blank=True)                   #default consent form used for new sessions
    institution = models.ManyToManyField(Institutions, through="ExperimentsInstitutions")                       #institutions to which this experiment belongs  
    budget_default = models.ForeignKey(User, on_delete=models.CASCADE, related_name='experiments_a', blank=True, null=True)             #default faculty budget for experiment
    experiment_pi = models.ForeignKey(User, on_delete=models.CASCADE,  related_name='experiments_b', blank=True, null=True)          #Primary Investigator

    title = models.CharField(max_length=300, default="***New Experiment***")                    #name of experimet 
    experiment_manager = models.CharField(max_length=300, default="***Manager Here***")         #faculty running experiment
    
    length_default = models.IntegerField(default=60)                                                       #default length of experiment
    notes = models.TextField(default="", null=True, blank=True)                                            #notes about the experiment
    showUpFee = models.DecimalField(decimal_places=6, max_digits=10, default=0)                            #amount subjects earn for attending by default
    special_instructions_default = models.CharField(max_length=300, default="", null=True, blank=True)     #special instructions for subject, ie online zoom meeting

    survey = models.BooleanField(default=False, verbose_name="Survey")              #experiment is a online survey

    archived = models.BooleanField(verbose_name="Archived", default=False)          #if archived hide from useage

    invitationText = HTMLField(default="")                 #text of email invitation subjects receive
    reminderText = HTMLField(default="")                   #text of email reminder subjects receive
    invite_to_all = models.BooleanField(verbose_name="Invite subjects to all sessions", default=False)          #if archived hide from useage

    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return mark_safe(str(self.title))
    
    class Meta:
        verbose_name = 'Experiment'
        verbose_name_plural = 'Experiments'

    #called when model form method is used
    def clean(self):
        for field in self._meta.fields:
                if isinstance(field, (models.CharField, models.TextField)):
                    if getattr(self, field.name):
                        setattr(self, field.name, getattr(self, field.name).strip()) 
    
    #check if experiment can be deleted
    def allowDelete(self):

        ES = self.ES.all()    

        for e in ES:
            if not e.allowDelete():
                return False

        return True

    #get string
    def getShowUpFeeString(self):
        return f'{self.showUpFee:0.2f}'

    #json object for experiment search
    def json_search(self):
        return{
            "id"  : self.id,
            "title": mark_safe(self.title),
            "experiment_manager":self.experiment_manager,
            "allowDelete":self.allowDelete(),
            "date":self.getDateRangeString(),
            "date_start":self.getDateString(),
        }

    #return date of range session of sessions
    def getDateRangeString(self):
        p = Parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)
        
        esd = main.models.ExperimentSessionDays.objects.filter(experiment_session__experiment=self).order_by('date')

        if len(esd) == 1:
            return  esd.first().date.astimezone(tz).strftime("%-m/%#d/%Y")
        
        if len(esd) > 1:
            return  f'{esd.first().date.astimezone(tz).strftime("%-m/%#d/%Y")} - {esd.last().date.astimezone(tz).strftime("%-m/%#d/%Y")}'

        return "No Sessions"
    
    #return any sessions that take place in the future
    def getFutureSessions(self):
        esd_list = main.models.ExperimentSessionDays.objects.filter(experiment_session__experiment=self).filter(date__gte=datetime.now()).values_list('experiment_session__id', flat=True)
        return self.ES.filter(id__in=esd_list).annotate(last_date=Max('ESD__date')).order_by('last_date')

    #return date of first session
    def getDateString(self):
        p = Parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)
        
        esd = main.models.ExperimentSessionDays.objects.filter(experiment_session__experiment=self).order_by('date').first()

        if esd:
            return  esd.date.astimezone(tz).strftime("%-m/%#d/%Y")

        return "No Sessions"
    
    #get last session day
    def getLastSessionDay(self):
        return main.models.ExperimentSessionDays.objects.filter(experiment_session__experiment=self).order_by('-date').first()

        #get last session day
    def getLastSessionDayDate(self):
        experiment_session_day = main.models.ExperimentSessionDays.objects.filter(experiment_session__experiment=self).order_by('-date').first()

        return experiment_session_day.date if experiment_session_day else None

    #return true if at least one subject in one session has confirmed
    def checkForConfirmation(self):
        for s in self.ES.all():
            if s.getConfirmedCount() > 0:
                return True

        return False

    #small json object
    def json_min(self):
        return{
            "id":self.id,
            "name": mark_safe(self.title),
        }
        
    #get json sessions from this experiment
    def json_sessions(self, offset=0, limit=10000):
        return{
             "experiment_sessions":[es.json_min() for es in self.ES.all()
                                      .annotate(first_date=models.Min("ESD__date"))
                                      .order_by('-first_date')[offset:limit]],
        }

    #get json object experiment
    def json(self):
        return{
            "id":self.id,
            "title":  mark_safe(self.title),
            "experiment_manager":self.experiment_manager,
            "consent_form_default":self.consent_form_default.id if self.consent_form_default else None,
            "consent_form_default_full":self.consent_form_default.json() if self.consent_form_default else None,
            "length_default":self.length_default,
            "notes":self.notes,
            "invitationText":self.invitationText,
            "reminderText":self.reminderText,
            "school":self.school.id,
            "showUpFee":self.showUpFee,
            "special_instructions_default":self.special_instructions_default,
            "school_full":self.school.json(),
            "account_default":self.account_default.id,
            "account_default_full":self.account_default.json(),   
            "budget_default":self.budget_default.id if self.budget_default else None,
            "budget_default_full":self.budget_default.profile.json_min() if self.budget_default else None,
            "experiment_pi":self.experiment_pi.id if self.experiment_pi else None,
            "experiment_pi_full":self.experiment_pi.profile.json_min() if self.experiment_pi else None,           
            "institution": [str(i.id) for i in self.institution.all()],
            "institution_full": [i.json() for i in self.institution.all().order_by('name')],    
            "confirmationFound":self.checkForConfirmation(),
            "survey": 1 if self.survey else 0,
            "invite_to_all":1 if self.invite_to_all else 0,
        }

#delete recruitment parameters when deleted
@receiver(post_delete, sender=Experiments)
def post_delete_recruitment_params_default(sender, instance, *args, **kwargs):
    if instance.recruitment_params_default: # just in case user is not specified
        instance.recruitment_params_default.delete()

#proxy model returns link to experiemnts
class hrefExperiments(Experiments): 
    class Meta:
        proxy = True

    def __str__(self):
        return mark_safe('<a href=\"/experiment/' + str(self.id) + '\" target=_self  >' + str(self.title) + '</a>')
    
