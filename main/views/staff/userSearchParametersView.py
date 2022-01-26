import json
import logging

from django.shortcuts import render
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import CharField, F, Value as V
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder

from main.decorators import user_is_staff

from main.models import experiments
from main.models import experiment_sessions
from main.models import parameters
from main.models import help_docs

from main.views.staff.experimentView import addSessionBlank
from main.views.staff.experimentSearchView import createExperimentBlank

from main.forms import recruitmentParametersForm

import main

@login_required
@user_is_staff
def userSearchParametersView(request, id=None):
    '''
    search for users using recruiment parameters
    '''
    status = ""      

    if request.method == 'POST':
        
        data = json.loads(request.body.decode('utf-8'))              

        if data["status"] == "search":
            return search(data)                     

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

        recruitment_params = {}

        if not id:
            #no experiment id provided, create dummy experiment
            with transaction.atomic():
                i1=main.models.institutions(name="search")
                i1.save()

                e = createExperimentBlank()
                e.institution.set([i1])
                e.save()

                recruitment_params = e.recruitment_params_default.json() 

                e.delete()
                i1.delete()
        else:
            try:
                e = experiments.objects.get(id=id)     
            except ObjectDoesNotExist :
                raise Http404('Experiment Not Found')   
            
            recruitment_params = e.recruitment_params_default.json() 

        return render(request,
                      'staff/userSearchParameters.html',
                      {'updateRecruitmentParametersForm':recruitmentParametersForm(),  
                       'recruitment_parameters_form_ids':recruitment_parameters_form_ids,  
                       'helpText':helpText,
                       'experiment_id':e.id if id else None,
                       'experiment_title':e.title if id else None,
                       'recruitment_params': json.dumps(recruitment_params, cls=DjangoJSONEncoder),
                       },)

def search(data):
    '''
    search for valid subjects based on recruiment parameters
    '''
    logger = logging.getLogger(__name__)
    logger.info(f"Update default recruitment parameters: {data}")

    with transaction.atomic():
        i1=main.models.institutions(name="search")
        i1.save()

        e = createExperimentBlank()
        e.institution.set([i1])
        e.save()

        form_data_dict = data["formData"]

        form = recruitmentParametersForm(form_data_dict, instance=e.recruitment_params_default)

        if form.is_valid():
            #print("valid form")                                
            form.save()    

            es = addSessionBlank(e)

            u_list = es.getValidUserList_forward_check([], False, 0, 0, [], False, 0)

            u_list_json = User.objects.filter(email__in = u_list).values('email', 'id')

            e.delete()
            i1.delete()
                                        
            return JsonResponse({"status":"success",
                                 "result": {"count":len(u_list),
                                            "u_list_json": list(u_list_json)}}, safe=False)
        else:
            print("invalid form2")

            e.delete()
            i1.delete()

            return JsonResponse({"status":"fail", "errors":dict(form.errors.items())}, safe=False)
        
        

    # genderList=[]
    # subject_typeList=[]
    # institutionsExcludeList=[]
    # institutionsIncludeList=[]
    # experimentsExcludeList=[]
    # experimentsIncludeList=[]
    # schoolsExcludeList=[]
    # schoolsIncludeList=[]

    # for field in data["formData"]:            
    #     if field["name"] == "gender":                 
    #         genderList.append(field["value"])
    #     elif field["name"] == "subject_type":                 
    #         subject_typeList.append(field["value"])
    #     elif field["name"] == "institutions_exclude":                 
    #         institutionsExcludeList.append(field["value"])
    #     elif field["name"] == "institutions_include":                 
    #         institutionsIncludeList.append(field["value"])
    #     elif field["name"] == "experiments_exclude":                 
    #         experimentsExcludeList.append(field["value"])
    #     elif field["name"] == "experiments_include":                 
    #         experimentsIncludeList.append(field["value"])
    #     elif field["name"] == "schools_exclude":                 
    #         schoolsExcludeList.append(field["value"])
    #     elif field["name"] == "schools_include":                 
    #         schoolsIncludeList.append(field["value"])
    #     else:
    #         form_data_dict[field["name"]] = field["value"]

    # form_data_dict["gender"]=genderList
    # form_data_dict["subject_type"]=subject_typeList
    # form_data_dict["institutions_exclude"]=institutionsExcludeList
    # form_data_dict["institutions_include"]=institutionsIncludeList
    # form_data_dict["experiments_exclude"]=experimentsExcludeList
    # form_data_dict["experiments_include"]=experimentsIncludeList
    # form_data_dict["schools_exclude"]=schoolsExcludeList
    # form_data_dict["schools_include"]=schoolsIncludeList

    #print(form_data_dict)
   

