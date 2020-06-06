from django.db import models
import logging
import traceback

from . import genders,subject_types,experience_levels,institutions,experiments

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