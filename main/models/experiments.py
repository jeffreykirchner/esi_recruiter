from django.db import models
import logging
import traceback

from . import schools,accounts,institutions,genders,subject_types,experience_levels,institutions

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