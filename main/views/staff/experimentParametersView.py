from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from main.decorators import user_is_staff
from main.models import experiment, \
                        experiment_session_day_users, \
                        experiment_sessions, \
                        institutions, \
                        experiments, \
                        parameters,\
                        experiment_session_messages,\
                        experiment_session_invitations,\
                        recruitment_parameters,\
                        help_docs,\
                        Recruitment_parameters_trait_constraint,\
                        Traits
from main.forms import recruitmentParametersForm, experimentSessionForm2, TraitConstraintForm
from django.http import JsonResponse
import json
import logging
from django.db.models import CharField, Q, F, Value as V, Subquery


#induvidual experiment view
@login_required
@user_is_staff
def experimentParametersView(request, id):
       
    status = ""      

    if request.method == 'POST':
        
        data = json.loads(request.body.decode('utf-8'))         

        try:
            e = experiment.objects.get(id=id)  
        except e.DoesNotExist:
            raise Http404('Experiment Not Found')               

        if data["status"] == "get":            
            return getExperiment(data,id)
        elif data["status"] == "updateRecruitmentParameters":
            return updateRecruitmentParameters(data,id)                     

    else: #GET             

        p = parameters.objects.first()

        try:
            helpText = help_docs.objects.annotate(rp = V(request.path,output_field=CharField()))\
                                        .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
             helpText = "No help doc was found."

        return render(request,
                      'staff/experimentSessionParameters.html',
                      {'updateRecruitmentParametersForm':recruitmentParametersForm(),    
                       'helpText':helpText,
                       'session':experiment_sessions.objects.get(id=id)})

#get session info the show screen at load
def getExperiment(data,id):
    logger = logging.getLogger(__name__)
    logger.info(f"get session paramters {data}")

    e = experiment.objects.get(id=id)
    
    # logger.info(es.recruitment_params)

    return JsonResponse({"session" : e.json(),
                         "recruitment_params":e.recruitment_params.json()}, safe=False)

#update the recruitment parameters for this session
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

