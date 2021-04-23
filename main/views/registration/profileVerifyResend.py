import logging
import json

from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login
from django import forms
from main.forms import verifyFormResend
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

import main

from main.models import profile
from main.globals import profile_create_send_email
from main.models import parameters


#user account info
@login_required
def profileVerifyResend(request):    

    if request.method == 'POST':
        # logger = logging.getLogger(__name__)
        # logger.info("Verify Email Resend POST")

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getUser":
            return getUser(request,data)
        elif data["action"] == "sendVerificationEmail":
            return sendVerificationEmail(request,data)

        return JsonResponse({"status":"fail"}, safe=False)
    else:

        return render(request,'registration/profileVerifyResend.html',{ })   

#get user status
def getUser(request,data):
    logger = logging.getLogger(__name__)
    logger.info("Get user")
    logger.info(data)

    u=request.user
    logger.info(u)

    p = parameters.objects.first()

    return JsonResponse({"emailVerified":False if u.profile.email_confirmed != "yes" else True,
                         "admainName":p.labManager.first_name + " " + p.labManager.last_name,
                         "adminEmail":p.labManager.email}, safe=False) 

#resend verifiction email link to user
def sendVerificationEmail(request, data):
    logger = logging.getLogger(__name__)
    logger.info("Send verification email")
    logger.info(data)

    user = request.user
    logger.info(user)

    status = ""

    try:
        result = profile_create_send_email(user)   
        status = "done"

        if result["mail_count"] == 0:
            status = "fail"
    except:
        status = "fail"

    return JsonResponse({"status":status}, safe=False)