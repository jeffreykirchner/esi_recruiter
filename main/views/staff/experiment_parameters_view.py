import json
import logging

from django.shortcuts import render
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import CharField, Q, F, Value as V
from django.core.exceptions import ObjectDoesNotExist
from django.views import View
from django.utils.decorators import method_decorator
from django.views.generic.detail import SingleObjectMixin

from main.decorators import user_is_staff

from main.models import Experiments
from main.models import Parameters
from main.models import HelpDocs

from main.forms import RecruitmentParametersForm

class ExperimentParametersView(SingleObjectMixin, View):
    '''
    Experiment default recruitment parameters setup
    '''

    template_name = "staff/experiment_parameters.html"
    model = Experiments

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

        return render(request,
                      self.template_name,
                      {'updateRecruitmentParametersForm':RecruitmentParametersForm(),  
                      'recruitment_parameters_form_ids':recruitment_parameters_form_ids,  
                       'helpText':helpText,
                       'experiment':self.get_object()})
    
    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__)

        data = json.loads(request.body.decode('utf-8'))         

        id =  self.get_object().id            

        if data["status"] == "get":            
            return getExperiment(data,id)
        elif data["status"] == "updateRecruitmentParameters":
            return updateRecruitmentParameters(data,id)

#get session info the show screen at load
def getExperiment(data,id):
    logger = logging.getLogger(__name__)
    logger.info(f"get session paramters {data}")

    e = Experiments.objects.get(id=id)
    
    # logger.info(es.recruitment_params)

    return JsonResponse({"experiment" : e.json(),
                         "recruitment_params":e.recruitment_params_default.json()}, safe=False)

#update the recruitment parameters for this session
def updateRecruitmentParameters(data,id):
    logger = logging.getLogger(__name__)
    logger.info(f"Update default recruitment parameters: {data}")

    e = Experiments.objects.get(id=id)

    form_data_dict = data["formData"]

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
    form = RecruitmentParametersForm(form_data_dict,instance=e.recruitment_params_default)

    if form.is_valid():
        #print("valid form")                                
        form.save()    
                                    
        return JsonResponse({"recruitment_params":e.recruitment_params_default.json(),"status":"success"}, safe=False)
    else:
        print("invalid form2")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

