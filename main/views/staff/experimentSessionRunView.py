from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
import logging

from main.models import experiment_session_days,experiment_session_day_users

@login_required
@user_is_staff
def experimentSessionRunView(request,id=None):
    logger = logging.getLogger(__name__) 
        
    # logger.info("some info")

    if request.method == 'POST':       

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getSession":
            return getSession(data,id)
        elif data["action"] == "attendSubject":
            return attendSubject(data,id)
        elif data["action"] == "bumpSubject":
            return bumpSubject(data,id)
        elif data["action"] == "noShowSubject":
            return noShowSubject(data,id)
           
        return JsonResponse({"response" :  "error"},safe=False)       
    else:      
        esd = experiment_session_days.objects.get(id=id)
        return render(request,'staff/experimentSessionRunView.html',{"sessionDay":esd ,"id":id})  

def getSession(data,id):    
    logger = logging.getLogger(__name__)
    logger.info("Get Session Day")
    logger.info(data)

    esd = experiment_session_days.objects.get(id=id)

    return JsonResponse({"sessionDay" : esd.json_runInfo() }, safe=False)

def attendSubject(data,id):    
    logger = logging.getLogger(__name__)
    logger.info("Attend Subject")
    logger.info(data)

    esdu = experiment_session_day_users.objects.get(id=data['id'])

    esdu.attended=True
    esdu.bumped=False
    esdu.save()

    esd = experiment_session_days.objects.get(id=id)

    return JsonResponse({"sessionDay" : esd.json_runInfo() }, safe=False)

def bumpSubject(data,id):    
    logger = logging.getLogger(__name__)
    logger.info("Bump Subject")
    logger.info(data)

    esdu = experiment_session_day_users.objects.get(id=data['id'])

    esdu.attended=False
    esdu.bumped=True
    esdu.save()

    esd = experiment_session_days.objects.get(id=id)

    return JsonResponse({"sessionDay" : esd.json_runInfo() }, safe=False)

def noShowSubject(data,id):    
    logger = logging.getLogger(__name__)
    logger.info("No Show")
    logger.info(data)

    esdu = experiment_session_day_users.objects.get(id=data['id'])

    esdu.attended=False
    esdu.bumped=False
    esdu.save()

    esd = experiment_session_days.objects.get(id=id)

    return JsonResponse({"sessionDay" : esd.json_runInfo()  }, safe=False)