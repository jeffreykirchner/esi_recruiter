from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from main.decorators import user_is_staff
from main.models import experiments, \
                        experiment_session_days, \
                        experiment_session_day_users, \
                        experiment_sessions, \
                        accounts, \
                        schools, \
                        institutions, \
                        genders, \
                        parameters,\
                        help_docs, \
                        Recruitment_parameters_trait_constraint,\
                        Traits,\
                        Invitation_email_templates
from main.forms import experimentForm1,recruitmentParametersForm,TraitConstraintForm,invitationEmailTemplateSelectForm
from django.http import JsonResponse
from django.core import serializers
from django.forms.models import model_to_dict
import json
from django.db.models import prefetch_related_objects
from django.urls import reverse
import logging
from django.db.models import Count, F, Value,CharField
from datetime import datetime,timedelta

@login_required
@user_is_staff
def experimentView(request,id):
    logger = logging.getLogger(__name__) 
       
    status = "" 

    if request.method == 'POST':
        
        data = json.loads(request.body.decode('utf-8'))         
        
        if data["status"] == "get":
            return getExperiment(data,id)          
        elif data["status"] == "update1":
            return updateForm1(data,id)                   
        elif data["status"] == "updateRecruitmentParameters":   
            return updateRecruitmentParameters(data,id)
        elif data["status"] == "add":
            return addSession(data,id)
        elif data["status"] == "remove":
            return removeSession(data,id)
        elif data["status"] == "addTrait":
            return addTrait(data,id)
        elif data["status"] == "deleteTrait":
            return deleteTrait(data,id)
        elif data["status"] == "updateTrait":
            return updateTrait(data,id)
        elif data["status"] == "updateRequireAllTraitContraints":
            return updateRequireAllTraitContraints(data,id)
        elif data["status"] == "fillInvitationTextFromTemplate":
            return fillInvitationTextFromTemplate(data,id)
        elif  data["status"] == "fillDefaultReminderText":
            return fillDefaultReminderText(data,id)
            

    else: #GET       

        try:
            helpText = help_docs.objects.annotate(rp = Value(request.path,output_field=CharField()))\
                                .filter(rp__icontains = F('path')).first().text
        except Exception  as e:   
            helpText = "No help doc was found."

        logger.info(request.path)

        return render(request,
                      'staff/experimentView.html',
                      {'form1':experimentForm1(),
                      'traitConstraintForm':TraitConstraintForm(),
                       'updateRecruitmentParametersForm':recruitmentParametersForm(),       
                       'invitationEmailTemplateForm' : invitationEmailTemplateSelectForm(), 
                       'invitationEmailTemplateForm_default':Invitation_email_templates.objects.filter(enabled=True).first().id,           
                       'id': id,
                       'helpText':helpText})

#get the eperiment info
def getExperiment(data,id):
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
def removeSession(data,id):
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
def addSession(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Add Session")
    logger.info(data) 

    status = ""

    e = experiments.objects.get(id=id) 

    #experiment must have an institution set before adding a session
    if len(e.institution.all()) == 0:
        status="Error: Please specify the institution parameter"
    else:
        es = addSessionBlank(e)

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
    #return JsonResponse({'url':reverse('experimentSessionView',args=(es.id,))},safe=False) 

#create empty experiment
def addSessionBlank(e):
    logger = logging.getLogger(__name__)
    logger.info("Add Session Blank")

    es=experiment_sessions()
    es.experiment=e    
    es.invitation_text = e.invitationText    
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

    form_data_dict["institution"] = institutionList                 

    form = experimentForm1(form_data_dict,instance=e)

    if form.is_valid():           
        e=form.save()               
        return JsonResponse({"experiment" : e.json(),"status":"success"}, safe=False)
    else:
        print("invalid form1")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

#update the default recruitment parameters        
def updateRecruitmentParameters(data,id):
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
    
