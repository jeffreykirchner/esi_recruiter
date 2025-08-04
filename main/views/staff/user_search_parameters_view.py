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
from django.views import View
from django.utils.decorators import method_decorator

from main.decorators import user_is_staff

from main.models import Experiments
from main.models import Parameters
from main.models import HelpDocs
from main.models import RecruitmentParametersTraitConstraint
from main.models import Traits

from main.globals import todays_date

from main.views.staff.experiment_view import addSessionBlank
from main.views.staff.experiment_search_view import createExperimentBlank

from main.forms import RecruitmentParametersForm
from main.forms import TraitConstraintForm

import main

class UserSearchParametersView(View):
    '''
    search for users that match recruitment paramters
    '''

    template_name = "staff/user_search_parameters.html"

    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logger = logging.getLogger(__name__)

        p = Parameters.objects.first()

        try:
            helpText = HelpDocs.objects.annotate(rp = V(request.path,output_field=CharField()))\
                                        .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
             helpText = "No help doc was found."
        
        recruitment_parameters_form = RecruitmentParametersForm()
        recruitment_parameters_form_ids=[]

        for i in recruitment_parameters_form:
            recruitment_parameters_form_ids.append(i.html_name)

        recruitment_params = {}

        id = kwargs.get('id', None)

        if not id:
            #no experiment id provided, create dummy experiment
            with transaction.atomic():
                i1=main.models.Institutions(name="search")
                i1.save()

                e = createExperimentBlank()
                e.institution.set([i1])
                e.save()

                recruitment_params = e.recruitment_params_default.json() 

                e.delete()
                i1.delete()
        else:
            try:
                e = Experiments.objects.get(id=id)     
            except ObjectDoesNotExist :
                raise Http404('Experiment Not Found')   
            
            recruitment_params = e.recruitment_params_default.json() 

        return render(request,
                      self.template_name,
                      {'updateRecruitmentParametersForm':RecruitmentParametersForm(),  
                       'recruitment_parameters_form_ids':recruitment_parameters_form_ids,  
                       'helpText':helpText,
                       'traitConstraintForm':TraitConstraintForm(),
                       'experiment_id':e.id if id else None,
                       'experiment_title':e.title if id else None,
                       'recruitment_params': json.dumps(recruitment_params, cls=DjangoJSONEncoder),
                       },)
    
    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__)

        data = json.loads(request.body.decode('utf-8'))           
        id = kwargs.get('id', None)   

        if data["status"] == "search":
            return search(request, data, id)

def search(request, data, id):
    '''
    search for valid subjects based on recruiment parameters
    '''
    logger = logging.getLogger(__name__)
    logger.info(f"Update default recruitment parameters: {data}")


    form_data_dict = data["formData"]  
    trait_data_list = data["trait_parameters"]
    trait_constraints_require_all = data["trait_constraints_require_all"]
    login_last_90_days = data["login_last_90_days"]

    if not request.user.is_staff:
        trait_data_list = []

    logger.info(f'trait_data_dict: {trait_data_list}')

    e = None
    es = None
    i1 = None

    if not id:
        #no experiment provided
        i1=main.models.Institutions(name="search")
        i1.save()

        e = createExperimentBlank()
        e.institution.set([i1])
        e.save()            

        form = RecruitmentParametersForm(form_data_dict, instance=e.recruitment_params_default)
    else:
        #experiment provided
        e = Experiments.objects.get(id=id)
        es = addSessionBlank(e)
        esd = es.ESD.first()
        esd.date = esd.date + timedelta(days=1000)

        es.recruitment_params.trait_constraints.all().delete()

        #traits
        es.recruitment_params.trait_constraints_require_all = trait_constraints_require_all
        es.recruitment_params.save()

        for i in trait_data_list:
            tc = RecruitmentParametersTraitConstraint()
            tc.recruitment_parameter = es.recruitment_params
            tc.trait = Traits.objects.get(id=i["trait"])
            tc.min_value = i["min_value"]
            tc.max_value = i["max_value"]
            tc.include_if_in_range = i["include_if_in_range"]
            tc.save()

        form = RecruitmentParametersForm(form_data_dict, instance=es.recruitment_params)

    if form.is_valid():
        #print("valid form")                       
        form.save()    

        if id:
            #experiment provided
            u_list = es.getValidUserList_forward_check([], False, 0, 0, [], False, 0)
            u_list_json = User.objects.filter(email__in = u_list)
            if login_last_90_days:
                u_list_json = u_list_json.filter(last_login__gte = todays_date() - timedelta(days=90))
            u_list_json = u_list_json.values('email', 'id')

            es.delete()                
        else:
            #no experiment provided

            es = addSessionBlank(e)

            #traits
            es.recruitment_params.trait_constraints_require_all = trait_constraints_require_all
            es.recruitment_params.save()
            for i in trait_data_list:
                tc = RecruitmentParametersTraitConstraint()
                tc.recruitment_parameter = es.recruitment_params
                tc.trait = Traits.objects.get(id=i["trait"])
                tc.min_value = i["min_value"]
                tc.max_value = i["max_value"]
                tc.include_if_in_range = i["include_if_in_range"]
                tc.save()

            esd = es.ESD.first()
            esd.date = esd.date + timedelta(days=1000)
            esd.save()

            u_list = es.getValidUserList_forward_check([], False, 0, 0, [], False, 0)
            u_list_json = User.objects.filter(email__in = u_list)
            if login_last_90_days:
                u_list_json = u_list_json.filter(last_login__gte = todays_date() - timedelta(days=90))
            u_list_json = u_list_json.values('email', 'id')

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
   

