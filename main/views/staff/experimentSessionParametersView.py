from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from main.decorators import user_is_staff
from main.models import experiment_sessions
from main.models import parameters,\
                        help_docs
from main.forms import recruitmentParametersForm, experimentSessionForm2, TraitConstraintForm
from django.http import JsonResponse
from django.forms.models import model_to_dict
import json
from django.conf import settings
import logging
from django.db.models import CharField, Q, F, Value as V, Subquery

#induvidual experiment view
@login_required
@user_is_staff
def experimentSessionParametersView(request, id):
       
    status = ""      

    if request.method == 'POST':
        
        data = json.loads(request.body.decode('utf-8'))         

        try:
            es = experiment_sessions.objects.get(id=id)  
        except es.DoesNotExist:
            raise Http404('Experiment Not Found')               

        if data["status"] == "get":            
            return getSesssion(data,id)
        elif data["status"] == "updateRecruitmentParameters":
            return updateRecruitmentParameters(data,id)                     

    else: #GET             

        p = parameters.objects.first()

        try:
            helpText = help_docs.objects.annotate(rp = V(request.path,output_field=CharField()))\
                                        .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
             helpText = "No help doc was found."

        recruitment_parameters_form = recruitmentParametersForm()
        recruitment_parameters_form_ids=[]
        for i in recruitment_parameters_form:
            recruitment_parameters_form_ids.append(i.html_name)

        return render(request,
                      'staff/experimentSessionParameters.html',
                      {'updateRecruitmentParametersForm':recruitment_parameters_form,    
                      'recruitment_parameters_form_ids':recruitment_parameters_form_ids,
                       'helpText':helpText,
                       'session':experiment_sessions.objects.get(id=id)})

#get session info the show screen at load
def getSesssion(data,id):
    logger = logging.getLogger(__name__)
    logger.info(f"get session paramters {data}")

    es = experiment_sessions.objects.get(id=id)
    
    # logger.info(es.recruitment_params)

    return JsonResponse({"session" : es.json(),
                         "recruitment_params":es.recruitment_params.json()}, safe=False)

#update the recruitment parameters for this session
def updateRecruitmentParameters(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Update recruitment form")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)
    
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

    #if a subject has confirmed cannot some parameters
    if es.getConfirmedCount() > 0:
        form_data_dict["allow_multiple_participations"] = "1" if es.recruitment_params.allow_multiple_participations else "0"

    #print(form_data_dict)
    form = recruitmentParametersForm(form_data_dict,instance=es.recruitment_params)

    if form.is_valid():
        #print("valid form")                
        form.save()               
        return JsonResponse({"recruitment_params":es.recruitment_params.json(),"status":"success"}, safe=False)
    else:
        logger.info("invalid recruitment form")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

