import json
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, F, Value, CharField
from django.db.models import Count
from django.views import View
from django.utils.decorators import method_decorator

from main.models import help_docs
from main.models import experiments
from main.models import experiment_sessions

from main.decorators import user_is_staff

from main.forms import ConsentFormReportForm

class ConsentFormReport(View):
    '''
    Open consent form report view
    '''

    template_name = "staff/consent_form_report.html"

    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    @method_decorator(staff_member_required)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logger = logging.getLogger(__name__)

        try:
            helpText = help_docs.objects.annotate(rp = Value(request.path,output_field=CharField()))\
                                        .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
             helpText = "No help doc was found."

        return render(request, self.template_name, {"helpText":helpText,
                                                    "consent_form_report_form":ConsentFormReportForm()})
    
    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    @method_decorator(staff_member_required)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__) 

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getConsentForm":
            return getConsentForm(data)
        
        return JsonResponse({"status" :  "error"},safe=False)    

#get a list of all open sessions
def getConsentForm(data):
    logger = logging.getLogger(__name__)
    logger.info(f"Get Consent Form: {data}")

    form_data_dict = {}

    for field in data["formData"]:            
        form_data_dict[field["name"]] = field["value"]
    
    form = ConsentFormReportForm(form_data_dict)

    subject_list=[]
    experiment_list=[]
    consent_form=None

    if form.is_valid():
        consent_form = form.cleaned_data['consent_form']

        subject_list = [i.json_report() for i in consent_form.profile_consent_forms_b.all()]

        consent_form_json = consent_form.json()

        experiment_ids = experiment_sessions.objects.filter(consent_form=consent_form) \
                                                    .values_list('experiment__id', flat=True)

        experiment_list = experiments.objects.filter(id__in=experiment_ids)

        experiment_list_json = [{"id":e.id, "title":e.title} for e in experiment_list]

    
    return JsonResponse({"subject_list" : subject_list,
                         "consent_form" : consent_form_json,
                         "experiment_list" : experiment_list_json,
                        },safe=False)