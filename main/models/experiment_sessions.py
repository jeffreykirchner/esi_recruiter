from django.db import models
import logging
import traceback
from django.urls import reverse
import main
import json
from django.core.serializers.json import DjangoJSONEncoder

from . import genders,subject_types,institutions,experiments,parameters,recruitmentParameters

#session for an experiment (could last multiple days)
class experiment_sessions(models.Model):
    experiment = models.ForeignKey(experiments,on_delete=models.CASCADE,related_name='ES')  
    showUpFee_legacy = models.DecimalField(decimal_places=6, max_digits=10,null = True) 
    canceled=models.BooleanField(default=False)

    recruitmentParams = models.ForeignKey(recruitmentParameters,on_delete=models.CASCADE,null=True)
    
    # #recruitment parameters    
    # registration_cutoff = models.IntegerField(default=1)    
    # actual_participants = models.IntegerField(default=1)
    # gender = models.ManyToManyField(genders)
    # subject_type =  models.ManyToManyField(subject_types)      

    # #institutions to include or exclude
    # institutions_exclude = models.ManyToManyField(institutions, related_name='%(class)s_institutions_exclude',blank=True)
    # institutions_include = models.ManyToManyField(institutions, related_name='%(class)s_institutions_include',blank=True)

    # #experiments to include or exclude
    # experiments_exclude = models.ManyToManyField(experiments, related_name='%(class)s_experiments_exclude',blank=True)
    # experiments_include = models.ManyToManyField(experiments, related_name='%(class)s_experiments_include',blank=True)

    # #range, in number of experiments, the subject has been in
    # experience_min = models.IntegerField(default = 0)
    # experience_max = models.IntegerField(default = 1000)
    # experience_constraint  =  models.BooleanField(default=False) 

    # #wether constraints should be be all or more than one
    # institutions_exclude_all = models.BooleanField(default=True)
    # institutions_include_all = models.BooleanField(default=True)
    # experiments_exclude_all = models.BooleanField(default=True)
    # experiments_include_all = models.BooleanField(default=True)

    # #all subject to come multiple times to the same same experiment
    # allow_multiple_participations =  models.BooleanField(default=False)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return "ID: " + self.id

    class Meta:
        verbose_name = 'Experiment Sessions'
        verbose_name_plural = 'Experiment Sessions'

    #get list of confirmed user emails
    def getConfirmedEmailList(self):

        l = main.models.experiment_session_day_users.objects.filter(experiment_session_day__experiment_session__id = self.id)\
                                                .filter(confirmed = True)\
                                                .select_related('user')\
                                                .values('user__email','user__id','user__first_name','user__last_name')\
                                                .order_by('user__email')\
                                                .distinct()   


        return [{"user_email": i['user__email'],
                 "user_id":i['user__id'],
                 "user_last_name":i['user__first_name'],
                 "user_first_name":i['user__last_name'],} for i in l ]

    #build an invitional email given the experiment session
    def getInvitationEmail(self):
       
        message = ""

        message = self.experiment.invitationText
        message = message.replace("[confirmation link]","http://www.google.com/")
        message = message.replace("[session length]",self.getSessionDayLengthString())
        message = message.replace("[session date and time]",self.getSessionDayDateString())
        message = message.replace("[on time bonus]","$" + self.experiment.getShowUpFeeString())

        return message
    
    #build a cancelation email for this experiment session
    def getCancelationEmail(self):
        p = parameters.parameters.objects.get(id=1)

        message = ""

        message = p.cancelationText
        message = message.replace("[session date and time]",self.getSessionDayDateString())

        return message

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

    #setup this session with defualt parameters from related experiment
    def setupRecruitment(self):

        p = self.experiment.recruitmentParamsDefault

        tempP = recruitmentParameters()
        tempP.save()

        self.recruitmentParams = tempP
        self.recruitmentParams.save()
        
        self.recruitmentParams.actual_participants = p.actual_participants
        self.recruitmentParams.registration_cutoff = p.registration_cutoff

        for i in p.gender.all():
            self.recruitmentParams.gender.add(i)
        
        for i in p.subject_type.all():
            self.recruitmentParams.subject_type.add(i)

        self.recruitmentParams.experience_min=p.experience_min
        self.recruitmentParams.experience_max=p.experience_max
        self.recruitmentParams.experience_constraint=p.experience_constraint

        for i in p.institutions_exclude.all():
            self.recruitmentParams.institutions_exclude.add(i)
        
        for i in p.institutions_include.all():
            self.recruitmentParams.institutions_include.add(i)

        for i in p.experiments_exclude.all():
            self.recruitmentParams.experiments_exclude.add(i)

        for i in p.experiments_include.all():
            self.recruitmentParams.experiments_include.add(i)

        self.recruitmentParams.institutions_exclude_all=p.institutions_exclude_all
        self.recruitmentParams.institutions_include_all=p.institutions_include_all
        self.recruitmentParams.experiments_exclude_all=p.experiments_exclude_all
        self.recruitmentParams.experiments_include_all=p.experiments_include_all

        self.recruitmentParams.allow_multiple_participations=p.allow_multiple_participations

        self.recruitmentParams.save()

        return self

    #check if this session can be deleted    
    def allowDelete(self):

        ESD = self.ESD.all()    

        for e in ESD:
            if not e.allowDelete():
                return False

        return True

    #get some of the json object
    def json_min(self):
        return{
            "id":self.id,
            "url": str(reverse('experimentSessionView',args=(self.id,))),           
            "experiment_session_days" : [esd.json_min() for esd in self.ESD.all().annotate(first_date=models.Min('date')).order_by('-first_date')],
            "allow_delete": self.allowDelete(),
        }
    
    #get session days attached to this session
    def json_esd(self,getUnConfirmed):
        return{          
            "experiment_session_days" : [esd.json(getUnConfirmed) for esd in self.ESD.all().annotate(first_date=models.Min('date')).order_by('-first_date')],
            "invitationText" : self.getInvitationEmail(),
            "confirmedEmailList" : self.getConfirmedEmailList(),
        }

    #get full json object
    def json(self):
        #days_list = self.ESD.order_by("-date").prefetch_related('experiment_session_day_users_set')

        return{
            "id":self.id,            
            "experiment":self.experiment.id,
            "canceled":self.canceled,
            #"actual_participants":self.actual_participants,
            #"registration_cutoff":self.registration_cutoff,
            "experiment_session_days" : [esd.json(False) for esd in self.ESD.all().annotate(first_date=models.Min('date')).order_by('-first_date')],
            #"experiment_session_days" : [esd.json() for esd in days_list],
            # "gender":[str(g.id) for g in self.gender.all()],
            # "gender_full":[g.json() for g in self.gender.all()],
            # "subject_type" : [str(st.id) for st in self.subject_type.all()],
            # "subject_type_full" : [st.json() for st in self.subject_type.all()],
            # "institutions_exclude" : [str(i.id) for i in self.institutions_exclude.all()],
            # "institutions_exclude_full" : [i.json() for i in self.institutions_exclude.all()],
            # "institutions_include" : [str(i.id) for i in self.institutions_include.all()],
            # "institutions_include_full" : [i.json() for i in self.institutions_include.all()],
            # "experiments_exclude" : [str(e.id) for e in self.experiments_exclude.all()],
            # "experiments_exclude_full" : [e.json_min() for e in self.experiments_exclude.all()],
            # "experiments_include" : [str(e.id) for e in self.experiments_include.all()],
            # "experiments_include_full" : [e.json_min() for e in self.experiments_include.all()],
            # "allow_delete": self.allowDelete(),
            # "experience_min":self.experience_min,
            # "experience_max":self.experience_max,
            # "experience_constraint":1 if self.experience_constraint else 0,
            # "institutions_exclude_all":1 if self.institutions_exclude_all else 0,
            # "institutions_include_all":1 if self.institutions_include_all else 0,
            # "experiments_exclude_all":1 if self.experiments_exclude_all else 0,
            # "experiments_include_all":1 if self.experiments_include_all else 0,
            # "allow_multiple_participations":1 if self.allow_multiple_participations else 0,
            "invitationText" : self.getInvitationEmail(),
            "cancelationText" : self.getCancelationEmail(),
            "confirmedEmailList" : self.getConfirmedEmailList(),
            "messageCount": self.experiment_session_messages_set.count(),
            "invitationCount": self.experiment_session_invitations_set.count(),
        }