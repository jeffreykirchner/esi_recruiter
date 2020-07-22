from django.db import models
import logging
import traceback
from django.urls import reverse

from . import genders,subject_types,institutions,experiments

#session for an experiment (could last multiple days)
class experiment_sessions(models.Model):
    experiment = models.ForeignKey(experiments,on_delete=models.CASCADE,related_name='ES')  
    showUpFee_legacy = models.DecimalField(decimal_places=6, max_digits=10,null = True) 

    #recruitment parameters
    actual_participants = models.IntegerField(default=1)
    registration_cutoff = models.IntegerField(default=1)    
    gender = models.ManyToManyField(genders)
    subject_type =  models.ManyToManyField(subject_types)      

    #institutions to include or exclude
    institutions_exclude = models.ManyToManyField(institutions, related_name='%(class)s_institutions_exclude',blank=True)
    institutions_include = models.ManyToManyField(institutions, related_name='%(class)s_institutions_include',blank=True)

    #experiments to include or exclude
    experiments_exclude = models.ManyToManyField(experiments, related_name='%(class)s_experiments_exclude',blank=True)
    experiments_include = models.ManyToManyField(experiments, related_name='%(class)s_experiments_include',blank=True)

    #range, in number of experiments, the subject has been in
    experience_min = models.IntegerField(default = 0)
    experience_max = models.IntegerField(default = 1000)
    experience_constraint  =  models.BooleanField(default=False) 

    #wether constraints should be be all or more than one
    institutions_exclude_all = models.BooleanField(default=True)
    institutions_include_all = models.BooleanField(default=True)
    experiments_exclude_all = models.BooleanField(default=True)
    experiments_include_all = models.BooleanField(default=True)

    #all subject to come multiple times to the same same experiment
    allow_multiple_participations =  models.BooleanField(default=False)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return "ID: " + self.id

    class Meta:
        verbose_name = 'Experiment Sessions'
        verbose_name_plural = 'Experiment Sessions'

    #add new user to session
    def addUser(self,userID):
        for esd in self.ESD.all():
            esd.addUser(userID)  

    #get a string of sessions day dates
    def getSessionDayDateString(self):
        tempS = ""

        ESD_list = list(self.ESD.all().order_by("date"))
        ESD_list_length=len(ESD_list)

        for i in ESD_list:
            if tempS != "":
                if ESD_list.index(i) == ESD_list_length-1:
                     tempS += " and "
                else:
                    tempS += ", "
        
            tempS += i.getDateString()
        
        return tempS

    #get a string of sessions day lengths
    def getSessionDayLengthString(self):
        tempS = ""

        ESD_list = list(self.ESD.all().order_by("date"))
        ESD_list_length=len(ESD_list)

        for i in ESD_list:
            if tempS != "":
                if ESD_list.index(i) == ESD_list_length-1:
                     tempS += " and "
                else:
                    tempS += ", "
        
            tempS += i.getLengthString()

        return tempS      
    
    def setupRecruitment(self):
        #setup this session with defualt parameters from related experiment

        self.actual_participants = self.experiment.actual_participants_default
        self.registration_cutoff = self.experiment.registration_cutoff_default

        for i in self.experiment.gender_default.all():
            self.gender.add(i)
        
        for i in self.experiment.subject_type_default.all():
            self.subject_type.add(i)

        self.experience_min=self.experiment.experience_min_default
        self.experience_max=self.experiment.experience_max_default
        self.experience_constraint=self.experiment.experience_constraint_default

        for i in self.experiment.institutions_exclude_default.all():
            self.institutions_exclude.add(i)
        
        for i in self.experiment.institutions_include_default.all():
            self.institutions_include.add(i)

        for i in self.experiment.experiments_exclude_default.all():
            self.experiments_exclude.add(i)

        for i in self.experiment.experiments_include_default.all():
            self.experiments_include.add(i)

        self.institutions_exclude_all=self.experiment.institutions_exclude_all_default
        self.institutions_include_all=self.experiment.institutions_include_all_default
        self.experiments_exclude_all=self.experiment.experiments_exclude_all_default
        self.experiments_include_all=self.experiment.experiments_include_all_default

        self.allow_multiple_participations=self.experiment.allow_multiple_participations_default

        return self

    #check if this session can be deleted    
    def allowDelete(self):

        ESD = self.ESD.all()    

        for e in ESD:
            if not e.allowDelete():
                return False

        return True

    def json_min(self):
        return{
            "id":self.id,
            "url": str(reverse('experimentSessionView',args=(self.id,))),           
            "experiment_session_days" : [esd.json_min() for esd in self.ESD.all().annotate(first_date=models.Min('date')).order_by('-first_date')],
            "allow_delete": self.allowDelete(),
        }
    
    #get session days attached to this session
    def json_esd(self):
        return{          
            "experiment_session_days" : [esd.json() for esd in self.ESD.all().annotate(first_date=models.Min('date')).order_by('-first_date')],
        }

    def json(self):
        return{
            "id":self.id,            
            "experiment":self.experiment.id,
            "actual_participants":self.actual_participants,
            "registration_cutoff":self.registration_cutoff,
            "experiment_session_days" : [esd.json() for esd in self.ESD.all().annotate(first_date=models.Min('date')).order_by('-first_date')],
            "gender":[str(g.id) for g in self.gender.all()],
            "gender_full":[g.json() for g in self.gender.all()],
            "subject_type" : [str(st.id) for st in self.subject_type.all()],
            "subject_type_full" : [st.json() for st in self.subject_type.all()],
            "institutions_exclude" : [str(i.id) for i in self.institutions_exclude.all()],
            "institutions_exclude_full" : [i.json() for i in self.institutions_exclude.all()],
            "institutions_include" : [str(i.id) for i in self.institutions_include.all()],
            "institutions_include_full" : [i.json() for i in self.institutions_include.all()],
            "experiments_exclude" : [str(e.id) for e in self.experiments_exclude.all()],
            "experiments_exclude_full" : [e.json_min() for e in self.experiments_exclude.all()],
            "experiments_include" : [str(e.id) for e in self.experiments_include.all()],
            "experiments_include_full" : [e.json_min() for e in self.experiments_include.all()],
            "allow_delete": self.allowDelete(),
            "experience_min":self.experience_min,
            "experience_max":self.experience_max,
            "experience_constraint":1 if self.experience_constraint else 0,
            "institutions_exclude_all":1 if self.institutions_exclude_all else 0,
            "institutions_include_all":1 if self.institutions_include_all else 0,
            "experiments_exclude_all":1 if self.experiments_exclude_all else 0,
            "experiments_include_all":1 if self.experiments_include_all else 0,
            "allow_multiple_participations":1 if self.allow_multiple_participations else 0,

        }