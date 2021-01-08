from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login
from django import forms
from main.forms import verifyFormResend
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from main.models import profile
from django.contrib.auth.decorators import login_required
import logging
import json
from django.http import JsonResponse
from main.models import parameters
import main

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

        return render(request,'profileVerifyResend.html',{ })   

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
def sendVerificationEmail(request,data):
    logger = logging.getLogger(__name__)
    logger.info("Send verification email")
    logger.info(data)

    u=request.user
    logger.info(u)

    status=""

    try:
        r = main.globals.profileCreateSendEmail(request,u)   
        status = "done"

        if r["mailCount"] == 0:
            status="fail"
    except:
        status = "fail"

    return JsonResponse({"status":status}, safe=False)