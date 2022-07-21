import pytz
import json
import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, F, Value, CharField
from django.db.models import Count
from django.views import View
from django.utils.decorators import method_decorator

from main.models import experiment_session_days
from main.models import help_docs
from main.models import parameters

from main.decorators import user_is_staff

class SessionsOpen(View):
    '''
    Open sessions view
    '''

    template_name = "staff/sessionsOpen.html"

    @method_decorator(login_required)
    @method_decorator(user_is_staff)
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

        return render(request, self.template_name, {"helpText":helpText,"id":""})
    
    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__) 

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getOpenSessions":
            return getOpenSessions(data)
        elif data["action"] == "closeAllSessions":
            return closeAllSessions(data)
        
        return JsonResponse({"status" :  "error"},safe=False)    

#get a list of all open sessions
def getOpenSessions(data):
    logger = logging.getLogger(__name__)
    logger.info("Get Open Sessions")
    logger.info(data)

    s_dict = experiment_session_days.objects.filter(complete = False).values('id',
                                                                             'date',
                                                                             'experiment_session__recruitment_params__registration_cutoff',
                                                                             'experiment_session__experiment__title',
                                                                             'experiment_session__id',
                                                                             'experiment_session__creator__id',
                                                                             'experiment_session__creator__last_name',
                                                                             'experiment_session__creator__first_name',
                                                                             'experiment_session__canceled',
                                                                             'experiment_session__budget__id',
                                                                             'experiment_session__budget__last_name',
                                                                             'experiment_session__budget__first_name',
                                                                             'experiment_session__experiment__id')\
                                                                     .annotate(invitation_count = Count('ESDU_b'))\
                                                                     .annotate(accepted_count = Count('ESDU_b',filter = Q(ESDU_b__confirmed=True)))\
                                                                     .order_by('date')
   
    s_list = list(s_dict)

    p = parameters.objects.first()
    tz = pytz.timezone(p.subjectTimeZone)

    for i in s_list:

        d = i["date"]
        i["date_str"] = d.astimezone(tz).strftime("%#m/%#d/%Y %#I:%M %p")

        

    logger.info(s_list)

    return JsonResponse({"sessions" : s_list},safe=False)

def closeAllSessions(data):
    logger = logging.getLogger(__name__)
    logger.info("Close All Sessions")
    logger.info(data)

    experiment_session_days.objects.all().update(complete = True)

    return getOpenSessions(data)
