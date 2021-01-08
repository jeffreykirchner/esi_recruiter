from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login
from django import forms
from main.forms import verifyForm
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from main.models import profile
from django.contrib.auth.decorators import login_required
import logging
import json
from django.http import JsonResponse
from main.models import parameters


#user account info
@login_required
def profileVerify(request,token):    
    status="update"            #either filling out the form or 
    
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "verifyEmail":
            return verifyEmail(request,data)        

        return JsonResponse({"status":"fail"}, safe=False)
    else:
       
        #check for correct token
        u = request.user
        failed=False
        if token != u.profile.email_confirmed or u.profile.email_confirmed == 'no':
            failed=True

        #check that user is not already verified
        emailVerified = True
        if u.profile.email_confirmed != 'yes':
            emailVerified = False

        return render(request,'profileVerify.html',{'emailVerified':emailVerified,
                                                    'failed':failed,    
                                                    'token':token,
                                                    'status':status})    

#verify user email address
def verifyEmail(request,data):
    logger = logging.getLogger(__name__)
    logger.info("Verify email")
    logger.info(data)

    emailVerified = True
    failed=False
    try:

        u=request.user                
        u.is_active=True
        u.profile.email_confirmed="yes"
        u.profile.paused=False
        u.profile.save()
        u.save()    

        status="done"            
    except ObjectDoesNotExist:
        print("Failed to validate email")
        emailVerified = False
        failed = False

    return JsonResponse({'emailVerified':emailVerified,
                         'failed':failed,}, safe=False)