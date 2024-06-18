import logging
import json

from django.shortcuts import render
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import CharField, F, Value as V
from django.views import View
from django.utils.decorators import method_decorator
from django.views.generic.detail import SingleObjectMixin

from main.models import ExperimentSessions
from main.models import Parameters
from main.models import HelpDocs

from main.forms import recruitmentParametersForm

from main.decorators import user_is_staff

class ExperimentSessionParametersView(SingleObjectMixin, View):
    '''
    edit experiment session recruitment parameters
    '''

    template_name = "staff/experiment_session_parameters.html"
    model = ExperimentSessions

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

        recruitment_parameters_form = recruitmentParametersForm()
        recruitment_parameters_form_ids=[]
        for i in recruitment_parameters_form:
            recruitment_parameters_form_ids.append(i.html_name)

        return render(request,
                      self.template_name,
                      {'updateRecruitmentParametersForm':recruitment_parameters_form,    
                       'recruitment_parameters_form_ids':recruitment_parameters_form_ids,
                       'helpText':helpText,
                       'session':self.get_object()})

    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__) 

        data = json.loads(request.body.decode('utf-8'))         

        id = self.get_object().id  

        if data["status"] == "get":            
            return getSesssion(data, id)
        elif data["status"] == "updateRecruitmentParameters":
            return updateRecruitmentParameters(data, id)

#get session info the show screen at load
def getSesssion(data,id):
    logger = logging.getLogger(__name__)
    logger.info(f"get session paramters {data}")

    es = ExperimentSessions.objects.get(id=id)
    
    # logger.info(es.recruitment_params)

    return JsonResponse({"session" : es.json(),
                         "recruitment_params":es.recruitment_params.json()}, safe=False)

#update the recruitment parameters for this session
def updateRecruitmentParameters(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Update recruitment form")
    logger.info(data)

    es = ExperimentSessions.objects.get(id=id)
    
    form_data_dict = data["formData"]

    #if a subject has confirmed cannot some parameters
    if es.getConfirmedCount() > 0:
        form_data_dict["allow_multiple_participations"] = 1 if es.recruitment_params.allow_multiple_participations else 0

    #print(form_data_dict)
    form = recruitmentParametersForm(form_data_dict,instance=es.recruitment_params)

    if form.is_valid():
        #print("valid form")                
        form.save()               
        return JsonResponse({"recruitment_params":es.recruitment_params.json(),"status":"success"}, safe=False)
    else:
        logger.info("invalid recruitment form")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

