from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
import logging
from main.models import experiment_session_days,help_docs
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.functions import Lower
from django.db.models import Q,F, Value,CharField
from django.db.models import Count
from django.shortcuts import redirect
import main

@login_required
@user_is_staff
def SessionsOpen(request):
    logger = logging.getLogger(__name__) 
    
    
    # logger.info("some info")

    if request.method == 'POST':       

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getOpenSessions":
            return getOpenSessions(data)
        elif data["action"] == "closeAllSessions":
            return closeAllSessions(data)
        
           
        return JsonResponse({"status" :  "error"},safe=False)       
    else:
        try:
            helpText = help_docs.objects.annotate(rp = Value(request.path,output_field=CharField()))\
                                        .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
             helpText = "No help doc was found."

        return render(request,'staff/sessionsOpen.html',{"helpText":helpText,"id":""})      

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
                                                                             'experiment_session__experiment__id')\
                                                                     .annotate(invitation_count = Count('experiment_session_day_users'))\
                                                                     .annotate(accepted_count = Count('experiment_session_day_users',filter = Q(experiment_session_day_users__confirmed=True)))\
                                                                     .order_by('date')
   
    s_list = list(s_dict)
    logger.info(s_list)

    return JsonResponse({"sessions" : s_list},safe=False)

def closeAllSessions(data):
    logger = logging.getLogger(__name__)
    logger.info("Close All Sessions")
    logger.info(data)

    experiment_session_days.objects.all().update(complete = True)

    return getOpenSessions(data)
