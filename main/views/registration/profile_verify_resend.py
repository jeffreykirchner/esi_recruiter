import logging
import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator

from main.globals import profile_create_send_email
from main.models import parameters

class ProfileVerifyResend(View):
    '''
    resend verification email
    '''

    template_name = "registration/profileVerifyResend.html"

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''
        return render(request,self.template_name,{ }) 
    
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getUser":
            return getUser(request, data)
        elif data["action"] == "sendVerificationEmail":
            return sendVerificationEmail(request, data)

        return JsonResponse({"status":"fail"}, safe=False)

#get user status
def getUser(request,data):
    logger = logging.getLogger(__name__)
    logger.info(f"Get user: {data}")

    u=request.user
    logger.info(u)

    p = parameters.objects.first()

    return JsonResponse({"emailVerified":False if u.profile.email_confirmed != "yes" else True,
                         "admainName":p.labManager.first_name + " " + p.labManager.last_name,
                         "adminEmail":p.labManager.email}, safe=False) 

#resend verifiction email link to user
def sendVerificationEmail(request, data):
    logger = logging.getLogger(__name__)
    logger.info(f"Send verification email: {data}")
    
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