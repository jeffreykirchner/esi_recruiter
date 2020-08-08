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

from main.models import experiment_session_days,experiment_session_day_users

@login_required
@user_is_staff
def experimentSessionPayoutsView(request,id=None,payGroup=None):
    logger = logging.getLogger(__name__) 
        
    # logger.info("some info")

    if request.method == 'POST':       

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getSession":
            return getSession(data,id,payGroup)
           
        return JsonResponse({"response" :  "error"},safe=False)       
    else:      
        esd = experiment_session_days.objects.get(id=id)
        return render(request,'staff/experimentSessionPayoutsView.html',{"sessionDay":esd ,"id":id})  

#return the session info to the client
def getSession(data,id,payGroup):    
    logger = logging.getLogger(__name__)
    logger.info("Get Session Day")
    logger.info(data)

    esd = experiment_session_days.objects.get(id=id)

    return JsonResponse({"sessionDay" : esd.json_runInfo() }, safe=False)