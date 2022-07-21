
import json
import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.views import View
from django.utils.decorators import method_decorator
from django.views.generic.detail import SingleObjectMixin

from django.db.models.functions import Lower

from main.decorators import user_is_staff

from main.models import experiment_session_days

class ExperimentSessionPayoutsView(SingleObjectMixin, View):
    '''
    Experiment session day paysheet view
    '''

    template_name = "staff/experimentSessionPayoutsView.html"
    model = experiment_session_days

    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logger = logging.getLogger(__name__)

        esd = self.get_object()
        payGroup = kwargs['payGroup']

        return render(request,
                      self.template_name,
                      {"sessionDay":esd,                      
                       "id":esd.id,
                       "consent_form" : json.dumps(esd.experiment_session.consent_form.json(), cls=DjangoJSONEncoder) if esd.experiment_session.consent_form else json.dumps(None,cls=DjangoJSONEncoder),
                       "payGroup":payGroup})
    
    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__) 

        data = json.loads(request.body.decode('utf-8'))

        id = esd = self.get_object().id

        if data["action"] == "getSession":
            return getSession(data, id, request.user)
           
        return JsonResponse({"response" :  "error"},safe=False)

#return the session info to the client
def getSession(data, id, request_user):    
    logger = logging.getLogger(__name__)
    logger.info("Get Session Day Payouts")    
    logger.info(data)

    payGroup = data["payGroup"]

    esd = experiment_session_days.objects.get(id=id)

    if payGroup == "bumps":     

        esd.users_who_printed_bumps.add(request_user)
        esd.save()

        esdu = esd.ESDU_b.filter(bumped = True)\
                         .order_by(Lower('user__last_name'), Lower('user__first_name'))

    elif payGroup == "payouts" or  payGroup == "consent":
        esd.users_who_printed_paysheet.add(request_user)
        esd.save()

        esdu = esd.ESDU_b.filter(attended = True)\
                         .order_by(Lower('user__last_name'), Lower('user__first_name')) 

    return JsonResponse({"sessionDayUsers" : [i.json_runInfo() for i in esdu],                         
                         "experiment_session_day" : esd.json_runInfo(request_user)}, safe=False)