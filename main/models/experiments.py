from django.db import models
import logging
import traceback
from django.utils.safestring import mark_safe
from django.utils import timezone
import pytz
from . import schools,accounts,institutions,genders,subject_types,institutions,recruitmentParameters,parameters
import main

#info for each experiment
class experiments(models.Model):    

    #experiment parameters
    school = models.ForeignKey(schools,on_delete=models.CASCADE)
    account_default = models.ForeignKey(accounts,on_delete=models.CASCADE)
    recruitmentParamsDefault = models.ForeignKey(recruitmentParameters,on_delete=models.CASCADE,null=True)

    actual_participants_legacy = models.IntegerField(default=1,null=True)
    registration_cutoff_legacy = models.IntegerField(default=1,null=True)

    institution = models.ManyToManyField(institutions,through = "experiments_institutions")

    title = models.CharField(max_length = 300)
    experiment_manager = models.CharField(max_length = 300)

    length_default = models.IntegerField()
    notes = models.TextField(default="")   
    showUpFee = models.DecimalField(decimal_places=6, max_digits=10,default = 0)
    invitationText = models.CharField(max_length = 10000,default = "")        

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return mark_safe(str(self.title))
    
    class Meta:
        verbose_name = 'Experiment'
        verbose_name_plural = 'Experiments'
    
    #called when model form method is used
    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                setattr(self, field.name, getattr(self, field.name).strip())

        #check if this session can be deleted    
    
    def allowDelete(self):

        ES = self.ES.all()    

        for e in ES:
            if not e.allowDelete():
                return False

        return True

    #get string
    def getShowUpFeeString(self):
        return f'{self.showUpFee:0.2f}'

    #small json object
    def json_min(self):
        return{
            "id":self.id,
            "name": mark_safe(self.title),
        }
    
    #json object for experiment search
    def json_search(self):
        return{
            "id"  : self.id,
            "title": mark_safe(self.title),
            "experiment_manager":self.experiment_manager,
            "allowDelete":self.allowDelete(),
            "date":self.getDateString(),
        }

    #return date of first session
    def getDateString(self):
        p = parameters.objects.get(id=1)
        tz = pytz.timezone(p.subjectTimeZone)
        
        esd = main.models.experiment_session_days.objects.filter(experiment_session__experiment = self).order_by('date').first()

        if esd:
            return  esd.date.astimezone(tz).strftime("%-m/%#d/%Y")
        else:
            return "No Sessions"

        

    #get json sessions from this experiment
    def json_sessions(self):
        return{
             "experiment_sessions":[es.json_min() for es in self.ES.all()
                                    .annotate(first_date=models.Min("ESD__date")).order_by('-first_date')],
        }

    #get json object experiment
    def json(self):
        return{
            "id":self.id,
            "title":  mark_safe(self.title),
            "experiment_manager":self.experiment_manager,
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
        }


#proxy model returns link to experiemnts
class hrefExperiments(experiments): 
    class Meta:
        proxy = True

    def __str__(self):
        return mark_safe('<a href=\"/experiment/' + str(self.id) + '\" target=_blank  >' + str(self.title) + '</a>')
    
