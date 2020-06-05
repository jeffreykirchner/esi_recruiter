from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from datetime import datetime
import uuid

import main
from . import *

class subject_types(models.Model):
    name = models.CharField(max_length = 300)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return self.name

    def json(self):
        return{
            "id":self.id,
            "name":self.name,
        }
       
#info for each experiment
class experiments(models.Model):
    #experiment parameters
    title = models.CharField(max_length = 300)
    experiment_manager = models.CharField(max_length = 300)
    registration_cutoff_default = models.IntegerField()
    actual_participants_default = models.IntegerField()
    length_default = models.IntegerField()
    notes = models.TextField(null=True)
    school = models.ForeignKey(schools,on_delete=models.CASCADE)
    account_default = models.ForeignKey(accounts,on_delete=models.CASCADE)    
    institution = models.ManyToManyField(institutions,through = "experiments_institutions")

    #default recruitment parameters
    gender_default = models.ManyToManyField(genders)
    subject_type_default =  models.ManyToManyField(subject_types)   
    experience_level_default = models.ForeignKey(experience_levels,on_delete=models.CASCADE)    
    institutions_exclude_default = models.ManyToManyField(institutions, related_name="%(class)s_institutions_exclude_default",blank=True)
    institutions_include_default = models.ManyToManyField(institutions, related_name="%(class)s_institutions_include_default",blank=True)
    experiments_exclude_default = models.ManyToManyField("self", related_name="%(class)s_experiments_exclude_default",blank=True)
    experiments_include_default = models.ManyToManyField("self", related_name="%(class)s_experiments_include_default",blank=True)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return str(self.title)
    
    def json_min(self):
        return{
            "id":self.id,
            "name":self.title,
        }
    
    def json_sessions(self):
        return{
             "experiment_sessions":[es.json_min() for es in self.experiment_sessions_set.all()
                                    .annotate(first_date=models.Min("experiment_session_days__date")).order_by('-first_date')],
        }
    
    def json(self):
        return{
            "id":self.id,
            "title":self.title,
            "experiment_manager":self.experiment_manager,
            "registration_cutoff_default":self.registration_cutoff_default,
            "actual_participants_default":self.actual_participants_default,
            "length_default":self.length_default,
            "notes":self.notes,
            "school":self.school.id,
            "school_full":self.school.json(),
            "account_default":self.account_default.id,
            "account_default_full":self.account_default.json(),            
            "institution": [str(i.id) for i in self.institution.all()],
            "institution_full": [i.json() for i in self.institution.all().order_by('name')],           
            "gender_default":[str(g.id) for g in self.gender_default.all()],
            "gender_default_full":[g.json() for g in self.gender_default.all()],
            "subject_type_default" : [str(st.id) for st in self.subject_type_default.all()],
            "subject_type_default_full" : [st.json() for st in self.subject_type_default.all()],
            "experience_level_default": self.experience_level_default.id,
            "experience_level_default_full": self.experience_level_default.json(),
            "institutions_exclude_default" : [str(i.id) for i in self.institutions_exclude_default.all()],
            "institutions_exclude_default_full" : [i.json() for i in self.institutions_exclude_default.all()],
            "institutions_include_default" : [str(i.id) for i in self.institutions_include_default.all()],
            "institutions_include_default_full" : [i.json() for i in self.institutions_include_default.all()],
            "experiments_exclude_default" : [str(e.id) for e in self.experiments_exclude_default.all()],
            "experiments_exclude_default_full" : [e.json_min() for e in self.experiments_exclude_default.all()],
            "experiments_include_default" : [str(e.id) for e in self.experiments_include_default.all()],
            "experiments_include_default_full" : [e.json_min() for e in self.experiments_include_default.all()],

        }

#intermediate table for experiments and institutions
class experiments_institutions(models.Model):
    experiment = models.ForeignKey(experiments,on_delete=models.CASCADE)
    institution = models.ForeignKey(institutions,on_delete=models.CASCADE)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

#session for an experiment (could last multiple days)
class experiment_sessions(models.Model):
    experiment = models.ForeignKey(experiments,on_delete=models.CASCADE)  

    #recruitment parameters
    gender = models.ManyToManyField(genders)
    subject_type =  models.ManyToManyField(subject_types)   
    experience_level = models.ForeignKey(experience_levels,on_delete=models.CASCADE,default="0")    
    institutions_exclude = models.ManyToManyField(institutions, related_name='%(class)s_institutions_exclude',blank=True)
    institutions_include = models.ManyToManyField(institutions, related_name='%(class)s_institutions_include',blank=True)
    experiments_exclude = models.ManyToManyField(experiments, related_name='%(class)s_experiments_exclude',blank=True)
    experiments_include = models.ManyToManyField(experiments, related_name='%(class)s_experiments_include',blank=True)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return self.id
    
    def setupRecruitment(self):
        for i in self.experiment.gender_default.all():
            self.gender.add(i)
        
        for i in self.experiment.subject_type_default.all():
            self.subject_type.add(i)

        self.experience_level=self.experiment.experience_level_default

        for i in self.experiment.institutions_exclude_default.all():
            self.institutions_exclude.add(i)
        
        for i in self.experiment.institutions_include_default.all():
            self.institutions_include.add(i)

        for i in self.experiment.experiments_exclude_default.all():
            self.experiments_exclude.add(i)

        for i in self.experiment.experiments_include_default.all():
            self.experiments_include.add(i)

        return self

    def json_min(self):
        return{
            "id":self.id,
            "url": str(reverse('experimentSession',args=(self.id,))),           
            "experiment_session_days" : [esd.json_min() for esd in self.experiment_session_days_set.all().annotate(first_date=models.Min('date')).order_by('-first_date')],
        }

    def json(self):
        return{
            "id":self.id,            
            "experiment":self.experiment.id,
            "experiment_session_days" : [esd.json() for esd in self.experiment_session_days_set.all().annotate(first_date=models.Min('date')).order_by('-first_date')],
            "gender":[str(g.id) for g in self.gender.all()],
            "gender_full":[g.json() for g in self.gender.all()],
            "subject_type" : [str(st.id) for st in self.subject_type.all()],
            "subject_type_full" : [st.json() for st in self.subject_type.all()],
            "experience_level": self.experience_level.id,
            "experience_level_full": self.experience_level.json(),
            "institutions_exclude" : [str(i.id) for i in self.institutions_exclude.all()],
            "institutions_exclude_full" : [i.json() for i in self.institutions_exclude.all()],
            "institutions_include" : [str(i.id) for i in self.institutions_include.all()],
            "institutions_include_full" : [i.json() for i in self.institutions_include.all()],
            "experiments_exclude" : [str(e.id) for e in self.experiments_exclude.all()],
            "experiments_exclude_full" : [e.json_min() for e in self.experiments_exclude.all()],
            "experiments_include" : [str(e.id) for e in self.experiments_include.all()],
            "experiments_include_full" : [e.json_min() for e in self.experiments_include.all()],
        }
    
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