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
                        parameters
from main.forms import experimentForm1,recruitmentParametersForm
from django.http import JsonResponse
from django.core import serializers
from django.forms.models import model_to_dict
import json
from django.db.models import prefetch_related_objects
from django.urls import reverse
import logging

@login_required
@user_is_staff
def experimentView(request,id):
       
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
    else: #GET       

        return render(request,
                      'staff/experimentView.html',
                      {'form1':experimentForm1(),
                       'updateRecruitmentParametersForm':recruitmentParametersForm(),                      
                       'id': id})

#get the eperiment info
def getExperiment(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Get Experiment")
    logger.info(data)

    try:
        e = experiments.objects.get(id=id)     
    except ObjectDoesNotExist :
        raise Http404('Experiment Not Found')

    p = parameters.objects.get(id=1)
            
    return JsonResponse({"experiment" :  e.json(),
                            "sessions" : e.json_sessions(),
                            "recruitmentParams":e.recruitmentParamsDefault.json(),
                            "parameters" : p.json()}, safe=False)

#delete session from experiment
def removeSession(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Remove session")
    logger.info(data)

    es = experiment_sessions.objects.get(id=data["sid"])

    logger.info("Recruitment Parameters ID:")
    logger.info(es.recruitmentParams)

    if es.allowDelete():        
        es.delete()

    e = experiments.objects.get(id=id) 

    return JsonResponse({"sessions" : e.json_sessions()}, safe=False)

#create experiment session, attach to experiment
def addSession(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Add Session")
    logger.info(data) 

    e = experiments.objects.get(id=id) 

    es=experiment_sessions()
    es.experiment=e           
    es.save()

    es.setupRecruitment()
    es.save()

    #create experiment session day, attach to session
    esd=experiment_session_days()
    esd.setup(es,[])
    esd.save()

    return JsonResponse({ "sessions" : e.json_sessions(),},safe=False)
    #return JsonResponse({'url':reverse('experimentSessionView',args=(es.id,))},safe=False) 

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
    subjectTypeList=[]
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
            subjectTypeList.append(field["value"])
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
    form_data_dict["subject_type"]=subjectTypeList
    form_data_dict["institutions_exclude"]=institutionsExcludeList
    form_data_dict["institutions_include"]=institutionsIncludeList
    form_data_dict["experiments_exclude"]=experimentsExcludeList
    form_data_dict["experiments_include"]=experimentsIncludeList
    form_data_dict["schools_exclude"]=schoolsExcludeList
    form_data_dict["schools_include"]=schoolsIncludeList

    #print(form_data_dict)
    form = recruitmentParametersForm(form_data_dict,instance=e.recruitmentParamsDefault)

    if form.is_valid():
        #print("valid form")                                
        form.save()    
                                    
        return JsonResponse({"recruitmentParams":e.recruitmentParamsDefault.json(),"status":"success"}, safe=False)
    else:
        print("invalid form2")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)    
    