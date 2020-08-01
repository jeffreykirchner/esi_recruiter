
from django.db import models
import logging

from . import genders,subject_types,institutions,experiments,experiment_sessions

class recruitmentParameters(models.Model):

    #recruitment parameters
    actual_participants = models.IntegerField(default=1,null=True)
    registration_cutoff = models.IntegerField(default=1,null=True)    
    gender = models.ManyToManyField(genders)
    subject_type =  models.ManyToManyField(subject_types)      

    #institutions to include or exclude
    institutions_exclude = models.ManyToManyField(institutions, related_name='%(class)s_institutions_exclude',blank=True)
    institutions_include = models.ManyToManyField(institutions, related_name='%(class)s_institutions_include',blank=True)

    #experiments to include or exclude
    experiments_exclude = models.ManyToManyField(experiments, related_name='%(class)s_experiments_exclude',blank=True)
    experiments_include = models.ManyToManyField(experiments, related_name='%(class)s_experiments_include',blank=True)

    #range, in number of experiments, the subject has been in
    experience_min = models.IntegerField(default = 0,null=True)
    experience_max = models.IntegerField(default = 1000,null=True)
    experience_constraint  =  models.BooleanField(default=False,null=True) 

    #wether constraints should be be all or more than one
    institutions_exclude_all = models.BooleanField(default=True,null=True)
    institutions_include_all = models.BooleanField(default=True,null=True)
    experiments_exclude_all = models.BooleanField(default=True,null=True)
    experiments_include_all = models.BooleanField(default=True,null=True)

    #all subject to come multiple times to the same same experiment
    allow_multiple_participations =  models.BooleanField(default=False,null=True)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated = models.DateTimeField(auto_now= True)   

    def __str__(self):
        return "ID: " + str(self.id)

    class Meta:                
        verbose_name = 'Recruitment Parameters'
        verbose_name_plural = 'Recruitment Parameters'

    def setup(self,es):
        self.save()

        self.actual_participants = es.actual_participants
        self.registration_cutoff = es.registration_cutoff

        self.gender.set(es.gender.all()) 
        self.subject_type.set(es.subject_type.all())

        self.institutions_exclude.set(es.institutions_exclude.all())
        self.institutions_include.set(es.institutions_include.all())

        self.experiments_exclude.set(es.experiments_exclude.all())
        self.experiments_include.set(es.experiments_include.all())

        self.experience_min = es.experience_min
        self.experience_max = es.experience_max
        self.experience_constraint = es.experience_constraint

        self.institutions_exclude_all = es.institutions_exclude_all
        self.institutions_include_all = es.institutions_include_all

        self.experiments_exclude_all = es.experiments_exclude_all
        self.experiments_include_all = es.experiments_include_all

        self.allow_multiple_participations = es.allow_multiple_participations

        self.save()

    def json_displayString(self):
        s=""

        s += "Genders: | "
        for g in self.gender.all():
            s +=  g.name + " | "
        s += "<br>"

        s += "Subject Types: | "
        for st in self.subject_type.all():
            s +=  st.name + " | "
        s += "<br>"

        s += "Number of Participants: "
        s += str(self.actual_participants)
        s += "<br>"

        s += "Registration Cutoff: "
        s += str(self.registration_cutoff)
        s += "<br>"

        if self.experience_constraint:
            s += "Experience Level: "
            s +=  str(self.experience_min) + " to " + str(self.experience_max)
            s += "<br>"

        s += "Allow Multiple Participations: "
        s += str(self.allow_multiple_participations)
        s += "<br>"

        s += "Include Institution Experience "
        if self.institutions_include_all:
            s+= "(All): | "
        else:
            s+= "(1+): | "       

        for st in self.institutions_include.all():
            s +=  st.name + " | "        
        s += "<br>"

        s += "Exclude Institution Experience "
        if self.institutions_exclude_all:
            s+= "(All): | "
        else:
            s+= "(1+): | "       

        for st in self.institutions_exclude.all():
            s +=  st.name + " | "        
        s += "<br>"

        s += "Include Experiment Experience "
        if self.experiments_include_all:
            s+= "(All): | "
        else:
            s+= "(1+): | "       

        for st in self.experiments_include.all():
            s +=  st.title + " | "        
        s += "<br>"

        s += "Exclude Experiment Experience "
        if self.experiments_exclude_all:
            s+= "(All): | "
        else:
            s+= "(1+): | "       

        for st in self.experiments_exclude.all():
            s +=  st.title + " | "        
        s += "<br>"

        return s

    def json(self):
        return{
            "id":self.id,
            "actual_participants":self.actual_participants,
            "registration_cutoff":self.registration_cutoff,
            "gender_full":[g.json() for g in self.gender.all()],
            "subject_type_full" : [st.json() for st in self.subject_type.all()],
            "institutions_exclude_full" : [i.json() for i in self.institutions_exclude.all()],
            "institutions_include_full" : [i.json() for i in self.institutions_include.all()],
            "experiments_exclude_full" : [e.json_min() for e in self.experiments_exclude.all()],
            "experiments_include_full" : [e.json_min() for e in self.experiments_include.all()],
            "experience_min":self.experience_min,
            "experience_max":self.experience_max,
            "experience_constraint":1 if self.experience_constraint else 0,
            "institutions_exclude_all":1 if self.institutions_exclude_all else 0,
            "institutions_include_all":1 if self.institutions_include_all else 0,
            "experiments_exclude_all":1 if self.experiments_exclude_all else 0,
            "experiments_include_all":1 if self.experiments_include_all else 0,
            "allow_multiple_participations":1 if self.allow_multiple_participations else 0,
        }