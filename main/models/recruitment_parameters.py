
from django.db import models
import logging

from  main.models import genders,subject_types,institutions,schools

import main

class recruitment_parameters(models.Model):

    #recruitment parameters
    actual_participants = models.IntegerField(default=1)
    registration_cutoff = models.IntegerField(default=1)    
    gender = models.ManyToManyField(genders)
    subject_type =  models.ManyToManyField(subject_types)      

    #institutions to include or exclude
    institutions_exclude = models.ManyToManyField(institutions, related_name='%(class)s_institutions_exclude',blank=True)
    institutions_include = models.ManyToManyField(institutions, related_name='%(class)s_institutions_include',blank=True)

    #experiments to include or exclude
    experiments_exclude = models.ManyToManyField('main.experiments', related_name='%(class)s_experiments_exclude',blank=True)
    experiments_include = models.ManyToManyField('main.experiments', related_name='%(class)s_experiments_include',blank=True)

    #range, in number of experiments, the subject has been in
    experience_min = models.IntegerField(default = 0,null=True)
    experience_max = models.IntegerField(default = 1000,null=True)
    experience_constraint  =  models.BooleanField(default=False) 

    #wether constraints should be be all or more than one
    institutions_exclude_all = models.BooleanField(default=True)
    institutions_include_all = models.BooleanField(default=True)
    experiments_exclude_all = models.BooleanField(default=True)
    experiments_include_all = models.BooleanField(default=True)

    #all subject to come multiple times to the same same experiment
    allow_multiple_participations =  models.BooleanField(default=False, null=True)

    #school filters by subject email domain
    schools_include = models.ManyToManyField(schools, blank=True, related_name='%(class)s_schools_include')
    schools_exclude = models.ManyToManyField(schools, blank=True, related_name='%(class)s_schools_exclude')
    schools_include_constraint = models.BooleanField(default=True)
    schools_exclude_constraint = models.BooleanField(default=False)

    #trait constraints
    trait_constraints_require_all = models.BooleanField(default=False)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated = models.DateTimeField(auto_now= True)   

    def __str__(self):
        return "ID: " + str(self.id)

    class Meta:                
        verbose_name = 'Recruitment Parameters'
        verbose_name_plural = 'Recruitment Parameters'

    def setup(self, es):
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

        self.schools_include.set(es.schools_include.all())
        self.schools_exclude.set(es.schools_exclude.all())
        self.schools_include_constraint = es.schools_include_constraint
        self.schools_exclude_constraint = es.schools_exclude_constraint

        #self.trait_constraints.set(es.trait_constraints.all())
        for trait_constraint in es.trait_constraints.all():
            new_trait_constraint = main.models.Recruitment_parameters_trait_constraint()

            new_trait_constraint.setup(trait_constraint)
            new_trait_constraint.recruitment_parameter = self
            new_trait_constraint.save()

        self.trait_constraints_require_all = es.trait_constraints_require_all

        self.save()

    #clear all of the parameters out
    #changing defaults will break tests
    def reset_settings(self):
        self.actual_participants = 1
        self.registration_cutoff =1 
        self.gender.clear()
        self.subject_type.clear()     

        #institutions to include or exclude
        self.institutions_exclude.clear()
        self.institutions_include.clear()

        #experiments to include or exclude
        self.experiments_exclude.clear()
        self.experiments_include.clear()

        #range, in number of experiments, the subject has been in
        self.experience_min = 0
        self.experience_max = 1000
        self.experience_constraint  =  False

        #wether constraints should be be all or more than one
        self.institutions_exclude_all = True
        self.institutions_include_all = True
        self.experiments_exclude_all = True
        self.experiments_include_all = True

        #all subject to come multiple times to the same same experiment
        self.allow_multiple_participations =  False

        self.schools_include.clear()
        self.schools_exclude.clear()
        self.schools_include_constraint=False
        self.schools_exclude_constraint=False

        #trait constraints
        self.trait_constraints.all().delete()
        self.trait_constraints_require_all = False

        self.save()

    #display string for recruietment history table
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

        s += "Trait Constraints "
        if self.trait_constraints_require_all:
           s+= "(All): | "
        else:
            s+= "(1+): | "

        for t in self.trait_constraints.all():
            mode = "Inc." if t.include_if_in_range else "Exc."
            s+= f'{t.trait.name} {mode} {t.min_value}-{t.max_value} | '
        s += "<br>"

        return s

    def trait_list(self):
        return [i.json() for i in self.trait_constraints.all()]

    def json(self):
        return{
            "id":self.id,
            "actual_participants":self.actual_participants,
            "registration_cutoff":self.registration_cutoff,
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
            "experience_min":self.experience_min,
            "experience_max":self.experience_max,
            "experience_constraint":1 if self.experience_constraint else 0,
            "institutions_exclude_all":1 if self.institutions_exclude_all else 0,
            "institutions_include_all":1 if self.institutions_include_all else 0,
            "experiments_exclude_all":1 if self.experiments_exclude_all else 0,
            "experiments_include_all":1 if self.experiments_include_all else 0,
            "allow_multiple_participations":1 if self.allow_multiple_participations else 0,
            "schools_include" : [str(i.id) for i in self.schools_include.all()],
            "schools_include_full" : [i.json() for i in self.schools_include.all()],
            "schools_exclude" : [str(i.id) for i in self.schools_exclude.all()],
            "schools_exclude_full" : [i.json() for i in self.schools_exclude.all()],
            "schools_include_constraint" : 1 if self.schools_include_constraint else 0,
            "schools_exclude_constraint" : 1 if self.schools_exclude_constraint else 0,
            "trait_constraints": self.trait_list(),
            "trait_constraints_require_all":self.trait_constraints_require_all,
        }