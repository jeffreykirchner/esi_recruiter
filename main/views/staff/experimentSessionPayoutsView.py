from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
import logging
from decimal import *
from django.db.models import Q,F
from django.http import HttpResponse
from django.db.models.functions import Lower

from main.models import experiment_session_days,experiment_session_day_users

@login_required
@user_is_staff
def experimentSessionPayoutsView(request,id=None,payGroup=None):
    logger = logging.getLogger(__name__) 
        
    # logger.info("some info")

    if request.method == 'POST':       

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getSession":
            return getSession(data,id)
           
        return JsonResponse({"response" :  "error"},safe=False)       
    else:      
        esd = experiment_session_days.objects.get(id=id)
        return render(request,'staff/experimentSessionPayoutsView.html',{"sessionDay":esd ,"id":id,"payGroup":payGroup})  

#return the session info to the client
def getSession(data,id):    
    logger = logging.getLogger(__name__)
    logger.info("Get Session Day Payouts")    
    logger.info(data)

    payGroup = data["payGroup"]

    esd = experiment_session_days.objects.get(id=id)

    if payGroup == "bumps":      
        esdu = esd.experiment_session_day_users_set.filter(bumped = True)\
                                                   .order_by(Lower('user__last_name'),Lower('user__first_name'))
    else:
        esdu = esd.experiment_session_day_users_set.filter(attended = True)\
                                                   .order_by(Lower('user__last_name'),Lower('user__first_name')) 

    return JsonResponse({"sessionDayUsers" : [i.json_runInfo() for i in esdu]}, safe=False)