from django.db import models
import logging
import traceback
from django.utils.safestring import mark_safe

from . import schools,accounts,institutions,genders,subject_types,institutions

#info for each experiment
class experiments(models.Model):    

    #experiment parameters
    school = models.ForeignKey(schools,on_delete=models.CASCADE)
    account_default = models.ForeignKey(accounts,on_delete=models.CASCADE)

    institution = models.ManyToManyField(institutions,through = "experiments_institutions")

    title = models.CharField(max_length = 300)
    experiment_manager = models.CharField(max_length = 300)
    registration_cutoff_default = models.IntegerField()
    actual_participants_default = models.IntegerField()
    length_default = models.IntegerField()
    notes = models.TextField(null=True)   
    showUpFee = models.DecimalField(decimal_places=6, max_digits=10,default = 0)
    invitationText = models.CharField(max_length = 10000,default = "")        
    
    #default recruitment parameters
    gender_default = models.ManyToManyField(genders)
    subject_type_default =  models.ManyToManyField(subject_types)  
    institutions_exclude_default = models.ManyToManyField(institutions, related_name="%(class)s_institutions_exclude_default",blank=True)
    institutions_include_default = models.ManyToManyField(institutions, related_name="%(class)s_institutions_include_default",blank=True)
    experiments_exclude_default = models.ManyToManyField("self", related_name="%(class)s_experiments_exclude_default",blank=True)
    experiments_include_default = models.ManyToManyField("self", related_name="%(class)s_experiments_include_default",blank=True)

    #min and max number of experiments a subject could be in
    experience_min_default = models.IntegerField(default = 0)
    experience_max_default = models.IntegerField(default = 1000)
    experience_constraint_default  =  models.BooleanField(default=False) 

    #wether constraints should be be all or more than one
    institutions_exclude_all_default = models.BooleanField(default=True)
    institutions_include_all_default = models.BooleanField(default=True)
    experiments_exclude_all_default = models.BooleanField(default=True)
    experiments_include_all_default = models.BooleanField(default=True)

    #all subject to come multiple times to the same same experiment
    allow_multiple_participations_default =  models.BooleanField(default=False)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return mark_safe(str(self.title))
    
    class Meta:
        verbose_name = 'Experiment'
        verbose_name_plural = 'Experiments'
    
    def getShowUpFeeString(self):
        return f'{self.showUpFee:0.2f}'

    def json_min(self):
        return{
            "id":self.id,
            "name": mark_safe(self.title),
        }
    
    def json_sessions(self):
        return{
             "experiment_sessions":[es.json_min() for es in self.ES.all()
                                    .annotate(first_date=models.Min("ESD__date")).order_by('-first_date')],
        }
    
    def json(self):
        return{
            "id":self.id,
            "title":  mark_safe(self.title),
            "experiment_manager":self.experiment_manager,
            "registration_cutoff_default":self.registration_cutoff_default,
            "actual_participants_default":self.actual_participants_default,
            "length_default":self.length_default,
            "notes":self.notes,
            "invitationText":self.invitationText,
            "school":self.school.id,
            "showUpFee":self.showUpFee,
            "school_full":self.school.json(),
            "account_default":self.account_default.id,
            "account_default_full":self.account_default.json(),            
            "institution": [str(i.id) for i in self.institution.all()],
            "institution_full": [i.json() for i in self.institution.all().order_by('name')],           
            "gender_default":[str(g.id) for g in self.gender_default.all()],
            "gender_default_full":[g.json() for g in self.gender_default.all()],
            "subject_type_default" : [str(st.id) for st in self.subject_type_default.all()],
            "subject_type_default_full" : [st.json() for st in self.subject_type_default.all()],
            "institutions_exclude_default" : [str(i.id) for i in self.institutions_exclude_default.all()],
            "institutions_exclude_default_full" : [i.json() for i in self.institutions_exclude_default.all()],
            "institutions_include_default" : [str(i.id) for i in self.institutions_include_default.all()],
            "institutions_include_default_full" : [i.json() for i in self.institutions_include_default.all()],
            "experiments_exclude_default" : [str(e.id) for e in self.experiments_exclude_default.all()],
            "experiments_exclude_default_full" : [e.json_min() for e in self.experiments_exclude_default.all()],
            "experiments_include_default" : [str(e.id) for e in self.experiments_include_default.all()],
            "experiments_include_default_full" : [e.json_min() for e in self.experiments_include_default.all()],
            "experience_min_default":self.experience_min_default,
            "experience_max_default":self.experience_max_default,
            "experience_constraint_default":1 if self.experience_constraint_default else 0,
            "institutions_exclude_all_default":1 if self.institutions_exclude_all_default else 0,
            "institutions_include_all_default":1 if self.institutions_include_all_default else 0,
            "experiments_exclude_all_default":1 if self.experiments_exclude_all_default else 0,
            "experiments_include_all_default":1 if self.experiments_include_all_default else 0,
            "allow_multiple_participations_default":1 if self.allow_multiple_participations_default else 0,
        }


#proxy model returns link to experiemnts
class hrefExperiments(experiments): 
    class Meta:
        proxy = True

    def __str__(self):
        return mark_safe('<a href=\"/experiment/' + str(self.id) + '\" target=_blank  >' + str(self.title) + '</a>')
    
