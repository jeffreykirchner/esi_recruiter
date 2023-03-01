from datetime import datetime, timedelta

import logging
import json
import re

from django.shortcuts import render
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, F, Value, CharField
from django.views import View
from django.utils.decorators import method_decorator
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.models import User

from main.decorators import user_is_staff

from main.models import experiments
from main.models import experiment_session_days
from main.models import experiment_sessions
from main.models import parameters
from main.models import help_docs
from main.models import Recruitment_parameters_trait_constraint
from main.models import Traits
from main.models import Invitation_email_templates

from main.forms import experimentForm1
from main.forms import recruitmentParametersForm
from main.forms import TraitConstraintForm
from main.forms import invitationEmailTemplateSelectForm

class ExperimentView(SingleObjectMixin, View):
    '''
    experiment view
    '''

    template_name = "staff/experimentView.html"
    model = experiments

    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logger = logging.getLogger(__name__)

        try:
            helpText = help_docs.objects.annotate(rp=Value(request.path, output_field=CharField()))\
                                .filter(rp__icontains=F('path')).first().text
        except Exception  as e:   
            helpText = "No help doc was found."

        id = self.get_object().id

        return render(request,
                      self.template_name,
                      {'form1':experimentForm1(),
                       'traitConstraintForm':TraitConstraintForm(),       
                       'invitationEmailTemplateForm' : invitationEmailTemplateSelectForm(), 
                       'invitationEmailTemplateForm_default':Invitation_email_templates.objects.filter(enabled=True).first().id,           
                       'id': id,
                       'helpText':helpText})
    
    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__) 

        data = json.loads(request.body.decode('utf-8'))

        id = self.get_object().id

        data = json.loads(request.body.decode('utf-8'))         
        
        if data["status"] == "get":
            return getExperiment(data, id)          
        elif data["status"] == "update1":
            return updateForm1(data, id)                   
        elif data["status"] == "updateRecruitmentParameters":   
            return updateRecruitmentParameters(data, id)
        elif data["status"] == "add":
            return addSession(data, id, request.user)
        elif data["status"] == "remove":
            return removeSession(data, id)
        elif data["status"] == "addTrait":
            return addTrait(data, id)
        elif data["status"] == "deleteTrait":
            return deleteTrait(data, id)
        elif data["status"] == "updateTrait":
            return updateTrait(data, id)
        elif data["status"] == "updateRequireAllTraitContraints":
            return updateRequireAllTraitContraints(data, id)
        elif data["status"] == "fillInvitationTextFromTemplate":
            return fillInvitationTextFromTemplate(data, id)
        elif  data["status"] == "fillDefaultReminderText":
            return fillDefaultReminderText(data, id)
        elif data["status"] == "addToAllowList":
           return addToAllowList(data, id)
        elif data["status"] == "clearAllowList":
           return clearAllowList(data, id)
            
#get the eperiment info
def getExperiment(data, id):
    logger = logging.getLogger(__name__)
    logger.info("Get Experiment")
    logger.info(data)

    try:
        e = experiments.objects.get(id=id)     
    except ObjectDoesNotExist :
        raise Http404('Experiment Not Found')

    p = parameters.objects.first()
            
    return JsonResponse({"experiment" :  e.json(),
                         "sessions" : e.json_sessions(),
                         "recruitment_params":e.recruitment_params_default.json(),
                           }, safe=False)

#delete session from experiment
def removeSession(data, id):
    logger = logging.getLogger(__name__)
    logger.info("Remove session")
    logger.info(data)

    es = experiment_sessions.objects.get(id=data["sid"])

    logger.info("Recruitment Parameters ID:")
    logger.info(es.recruitment_params)

    if es.allowDelete():        
        es.delete()

    e = experiments.objects.get(id=id) 

    return JsonResponse({"sessions" : e.json_sessions()}, safe=False)

#create experiment session, attach to experiment
def addSession(data, id, creator):
    logger = logging.getLogger(__name__)
    logger.info(f"Add Session: {data}")

    status = ""

    e = experiments.objects.get(id=id) 

    #experiment must have an institution set before adding a session
    if len(e.institution.all()) == 0:
        status="Error: Please specify the institution parameter"
    else:
        es = addSessionBlank(e)
        es.creator = creator
        es.save()

        #set default date time 1 day after last session day, to get it to top of list
        lastSD = es.experiment.getLastSessionDay()

        if lastSD:

            esd = es.ESD.first()
            newDate = lastSD.date + timedelta(days=1) + timedelta(hours=2)
            if esd.date < newDate:
                esd.date = newDate
                
            esd.set_end_date()
            esd.reminder_time = esd.date - timedelta(days=1)
            esd.save()

    return JsonResponse({ "sessions" : e.json_sessions(),"status":status},safe=False)

#create empty experiment
def addSessionBlank(e):
    logger = logging.getLogger(__name__)
    logger.info("Add Session Blank")

    e.save()

    es=experiment_sessions()
    es.experiment=e    
    es.invitation_text = e.invitationText    
    es.consent_form = e.consent_form_default
    es.budget = e.budget_default
    es.save()

    es.setupRecruitment()
    es.save()    

    #create experiment session day, attach to session
    esd=experiment_session_days()
    esd.setup(es,[])
    esd.save()

    return es

#update experiment parameters
def updateForm1(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Update experiment parameters")
    logger.info(data)

    e = experiments.objects.get(id=id)

    form_data_dict = {} 
    institutionList=[]               

    for field in data["formData"]:            
        if field["name"] == "institution":
            institutionList.append(field["value"])                
        else:
            form_data_dict[field["name"]] = field["value"]
    
    #if a subject has confirmed cannot change insitutions
    if e.checkForConfirmation():
           
        institutionList=[]
        for i in e.institution.all():
            institutionList.append(str(i.id))  

        form_data_dict["survey"] = 'true' if e.survey else 'false'
            

    form_data_dict["institution"] = institutionList                 

    form = experimentForm1(form_data_dict,instance=e)

    if form.is_valid():           
        e=form.save()               
        return JsonResponse({"experiment" : e.json(),"status":"success"}, safe=False)
    else:
        print("invalid form1")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

#update the default recruitment parameters        
def updateRecruitmentParameters(data, id):
    logger = logging.getLogger(__name__)
    logger.info("Update default recruitment parameters")
    logger.info(data)

    e = experiments.objects.get(id=id)

    form_data_dict = {} 

    genderList=[]
    subject_typeList=[]
    institutionsExcludeList=[]
    institutionsIncludeList=[]
    experimentsExcludeList=[]
    experimentsIncludeList=[]
    schoolsExcludeList=[]
    schoolsIncludeList=[]

    for field in data["formData"]:            
        if field["name"] == "gender":                 
            genderList.append(field["value"])
        elif field["name"] == "subject_type":                 
            subject_typeList.append(field["value"])
        elif field["name"] == "institutions_exclude":                 
            institutionsExcludeList.append(field["value"])
        elif field["name"] == "institutions_include":                 
            institutionsIncludeList.append(field["value"])
        elif field["name"] == "experiments_exclude":                 
            experimentsExcludeList.append(field["value"])
        elif field["name"] == "experiments_include":                 
            experimentsIncludeList.append(field["value"])
        elif field["name"] == "schools_exclude":                 
            schoolsExcludeList.append(field["value"])
        elif field["name"] == "schools_include":                 
            schoolsIncludeList.append(field["value"])
        else:
            form_data_dict[field["name"]] = field["value"]

    form_data_dict["gender"]=genderList
    form_data_dict["subject_type"]=subject_typeList
    form_data_dict["institutions_exclude"]=institutionsExcludeList
    form_data_dict["institutions_include"]=institutionsIncludeList
    form_data_dict["experiments_exclude"]=experimentsExcludeList
    form_data_dict["experiments_include"]=experimentsIncludeList
    form_data_dict["schools_exclude"]=schoolsExcludeList
    form_data_dict["schools_include"]=schoolsIncludeList

    #print(form_data_dict)
    form = recruitmentParametersForm(form_data_dict,instance=e.recruitment_params_default)

    if form.is_valid():
        #print("valid form")                                
        form.save()    
                                    
        return JsonResponse({"recruitment_params":e.recruitment_params_default.json(),"status":"success"}, safe=False)
    else:
        print("invalid form2")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)    

#add new trait constraint to parameters
def addTrait(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Add Trait Constraint")
    logger.info(data)

    e = experiments.objects.get(id=id)

    tc = Recruitment_parameters_trait_constraint()
    tc.recruitment_parameter = e.recruitment_params_default
    tc.trait = Traits.objects.first()
    tc.save()

    return JsonResponse({"recruitment_params":e.recruitment_params_default.json(),"status":"success"}, safe=False)

#delete trait constraint
def deleteTrait(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Delete Trait Constraint")
    logger.info(data)

    e = experiments.objects.get(id=id)

    t_id = data["id"]

    tc = Recruitment_parameters_trait_constraint.objects.filter(id=t_id)

    if tc:
        tc.first().delete()

    return JsonResponse({"recruitment_params":e.recruitment_params_default.json(),"status":"success"}, safe=False)

#update trait
def updateTrait(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Update Trait Constraint")
    logger.info(data)

    e = experiments.objects.get(id=id)

    t_id = data["trait_id"]

    tc = Recruitment_parameters_trait_constraint.objects.get(id=t_id)

    form_data_dict = {} 

    for field in data["formData"]:
        form_data_dict[field["name"]] = field["value"]

    form = TraitConstraintForm(form_data_dict,instance=tc)

    if form.is_valid():
                                    
        form.save()    
                                    
        return JsonResponse({"recruitment_params":e.recruitment_params_default.json(),"status":"success"}, safe=False)
    else:
        print("invalid form2")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

#update requireAllTraitContraints
def updateRequireAllTraitContraints(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Update Require All Trait Constraints")
    logger.info(data)

    e = experiments.objects.get(id=id)

    v = data["value"]

    if v==True:
        e.recruitment_params_default.trait_constraints_require_all=True
    else:
        e.recruitment_params_default.trait_constraints_require_all=False
    
    e.recruitment_params_default.save()
    e = experiments.objects.get(id=id)
    
    return JsonResponse({"recruitment_params":e.recruitment_params_default.json(),"status":"success"}, safe=False)

#fill invitation text from template
def fillInvitationTextFromTemplate(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Fill invitation text from template")
    logger.info(data)

    t = Invitation_email_templates.objects.filter(id = data["value"])

    text = ""

    if t.count() > 0:
        text = t.first().body_text
    
    return JsonResponse({"text":text}, safe=False)

#fill default reminder text
def fillDefaultReminderText(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Fill default reminder text")
    logger.info(data)

    p = parameters.objects.first()

    text = p.reminderText
    
    return JsonResponse({"text":text}, safe=False)

#update subjects allowed in session
def addToAllowList(data, id):
    logger = logging.getLogger(__name__)
    logger.info(f"addToAllowList session: {data}")

    form_data_dict = data["formData"]

    message = ""

    user_id_list = User.objects.all().values_list('id', flat=True)
    not_found_list = []

    try:

        #parse incoming file
        v=form_data_dict["allowed_list"].splitlines()

        id_list = []

        for i in range(len(v)):
            v[i] = re.split(r',|\t',v[i])

            for j in v[i]:
                temp_id = int(j)
                if temp_id not in id_list:

                    #check that vaid user id
                    if temp_id not in user_id_list:
                        not_found_list.append(temp_id)
                    else:
                        id_list.append(temp_id)

    except ValueError as e:
        message = f"Failed to load earnings: Invalid ID format"
        logger.info(message)
    except Exception as e:
        message = f"Failed to load earnings: {e}"
        logger.info(message)

    logger.info(f"addToAllowList found: {id_list}")
    logger.info(f"addToAllowList not found: {not_found_list}")

    if len(not_found_list) > 0:
        return JsonResponse({"not_found_list" : not_found_list,
                             "status" : "fail"}, safe=False)
                   
    experiment = experiments.objects.get(id=id)

    for i in id_list:
        if not experiment.recruitment_params_default.allowed_list:
            experiment.recruitment_params_default.allowed_list = []

        if i not in experiment.recruitment_params_default.allowed_list:
            experiment.recruitment_params_default.allowed_list.append(i)
    
    experiment.recruitment_params_default.save()

    return JsonResponse({"recruitment_params" : experiment.recruitment_params_default.json(), "status" : "success"}, safe=False)

#allow all subjects into session
def clearAllowList(data, id):
    logger = logging.getLogger(__name__)
    logger.info(f"clearAllowList session: {data}")

    s = experiment_sessions.objects.get(id=id)

    form_data_dict = data["formData"]

    experiment_session = experiment_sessions.objects.get(id=id)

    experiment_session.recruitment_params.allowed_list = []
    experiment_session.recruitment_params.save()
                   
    return JsonResponse({"recruitment_params" : experiment_session.recruitment_params.json(), "status":"success"}, safe=False)
    
