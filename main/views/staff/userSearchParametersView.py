from datetime import timedelta

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
from main.models import Recruitment_parameters_trait_constraint
from main.models import Traits

from main.views.staff.experimentView import addSessionBlank
from main.views.staff.experimentSearchView import createExperimentBlank

from main.forms import recruitmentParametersForm
from main.forms import TraitConstraintForm

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
            return search(data, id)                     

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
                       'traitConstraintForm':TraitConstraintForm(),
                       'experiment_id':e.id if id else None,
                       'experiment_title':e.title if id else None,
                       'recruitment_params': json.dumps(recruitment_params, cls=DjangoJSONEncoder),
                       },)

def search(data, id):
    '''
    search for valid subjects based on recruiment parameters
    '''
    logger = logging.getLogger(__name__)
    #logger.info(f"Update default recruitment parameters: {data}")

    with transaction.atomic():    

        form_data_dict = data["formData"]  
        trait_data_list = data["trait_parameters"]
        trait_constraints_require_all = data["trait_constraints_require_all"]

        logger.info(f'trait_data_dict: {trait_data_list}')

        e = None
        es = None
        i1 = None

        if not id:
            #no experiment provided
            i1=main.models.institutions(name="search")
            i1.save()

            e = createExperimentBlank()
            e.institution.set([i1])
            e.save()            

            form = recruitmentParametersForm(form_data_dict, instance=e.recruitment_params_default)
        else:
            #experiment provided
            e = experiments.objects.get(id=id)
            es = addSessionBlank(e)
            esd = es.ESD.first()
            esd.date = esd.date + timedelta(days=1000)

            #traits
            es.recruitment_params.trait_constraints_require_all = trait_constraints_require_all
            for i in trait_data_list:
                tc = Recruitment_parameters_trait_constraint()
                tc.recruitment_parameter = es.recruitment_params
                tc.trait = Traits.objects.get(id=i["trait_id"])
                tc.min_value = i["min_value"]
                tc.max_value = i["max_value"]
                tc.include_if_in_range = i["include_if_in_range"]
                tc.save()

            form = recruitmentParametersForm(form_data_dict, instance=es.recruitment_params)

        if form.is_valid():
            #print("valid form")                       
            form.save()    

            if id:
                #experiment provided
                u_list = es.getValidUserList_forward_check([], False, 0, 0, [], False, 0)
                u_list_json = User.objects.filter(email__in = u_list).values('email', 'id')

                es.delete()                
            else:
                #no experiment provided

                es = addSessionBlank(e)

                #traits
                es.recruitment_params.trait_constraints_require_all = True if trait_constraints_require_all=='true' else False

                for i in trait_data_list:
                    tc = Recruitment_parameters_trait_constraint()
                    tc.recruitment_parameter = es.recruitment_params
                    tc.trait = Traits.objects.get(id=i["trait_id"])
                    tc.min_value = i["min_value"]
                    tc.max_value = i["max_value"]
                    tc.include_if_in_range = i["include_if_in_range"]
                    tc.save()

                esd = es.ESD.first()
                esd.date = esd.date + timedelta(days=1000)
                esd.save()

                u_list = es.getValidUserList_forward_check([], False, 0, 0, [], False, 0)
                u_list_json = User.objects.filter(email__in = u_list).values('email', 'id')

                e.delete()
                i1.delete()
                                        
            return JsonResponse({"status":"success",
                                 "result": {"count":len(u_list),
                                            "u_list_json": list(u_list_json)}}, safe=False)
        else:
            print("invalid form2")

            if id:
                #experiment provided
                if es:
                    es.delete()
            else:
                #no experiment provided
                if e:
                    e.delete()
                    i1.delete()

            return JsonResponse({"status":"fail", "errors":dict(form.errors.items())}, safe=False)
   

