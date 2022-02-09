
import json
import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder

from django.db.models.functions import Lower

from main.decorators import user_is_staff

from main.models import experiment_session_days

@login_required
@user_is_staff
def experimentSessionPayoutsView(request, id=None, payGroup=None):
    logger = logging.getLogger(__name__) 
        
    # logger.info("some info")

    if request.method == 'POST':       

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getSession":
            return getSession(data, id, request.user)
           
        return JsonResponse({"response" :  "error"},safe=False)       
    else:      
        esd = experiment_session_days.objects.get(id=id)

        return render(request,
                     'staff/experimentSessionPayoutsView.html',
                      {"sessionDay":esd,
                       "experiment_session_day_json" : json.dumps(esd.json_runInfo(request.user), cls=DjangoJSONEncoder),
                       "id":id,
                       "payGroup":payGroup})  

#return the session info to the client
def getSession(data, id, request_user):    
    logger = logging.getLogger(__name__)
    logger.info("Get Session Day Payouts")    
    logger.info(data)

    payGroup = data["payGroup"]

    esd = experiment_session_days.objects.get(id=id)

    if payGroup == "bumps":      
        if not esd.complete:
            esd.user_who_printed_bumps = request_user
            esd.save()

        esdu = esd.experiment_session_day_users_set.filter(bumped = True)\
                                                   .order_by(Lower('user__last_name'), Lower('user__first_name'))
    else:
        if not esd.complete:
            esd.user_who_printed_paysheet = request_user
            esd.save()

        esdu = esd.experiment_session_day_users_set.filter(attended = True)\
                                                   .order_by(Lower('user__last_name'), Lower('user__first_name')) 

    return JsonResponse({"sessionDayUsers" : [i.json_runInfo() for i in esdu],
                         "experiment_session_day" : esd.json_runInfo(request_user)}, safe=False)