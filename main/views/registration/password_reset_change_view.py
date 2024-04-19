import uuid
import json
import logging

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import logout
from django.views import View

from main.models import parameters
from main.models import profile

from main.forms import passwordResetChangeForm

class PasswordResetChangeView(View):
    '''
    Password reset change view
    '''

    template_name = "registration/passwordResetChange.html"

    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logger = logging.getLogger(__name__) 

        token = kwargs['token']

        logout(request)

        p = parameters.objects.first()
        labManager = p.labManager 

        form = passwordResetChangeForm()

        form_ids=[]
        for i in form:
            form_ids.append(i.html_name)

        #check that code is valid
        valid_code_profile = checkValidCode(token)

        return render(request,self.template_name,{"labManager":labManager,
                                                  "form":form,
                                                  "token":token,
                                                  "valid_code":False if not valid_code_profile else True,
                                                  "form_ids":form_ids})
    
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__) 

        data = json.loads(request.body.decode('utf-8'))
        token = kwargs['token']

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "change_password":
            return changePassword(request, data, token)

        return JsonResponse({"response" :  "error"}, safe=False)
        
def checkValidCode(token):
    logger = logging.getLogger(__name__) 

    try:
        p = profile.objects.filter(password_reset_key = token)

        if p.count() != 1:
            logger.warning(f"Password reset failed for {token}, count: {p.count()}")
            return None
        else:
            return p.first()
    except:
        logger.warning(f"Password reset invalid code format {token}")
        return None


def changePassword(request,data,token):
    logger = logging.getLogger(__name__) 
   
    p = parameters.objects.first()

    #convert form into dictionary
    form_data_dict = data["formData"]             

    # for field in data["formData"]:            
    #     form_data_dict[field["name"]] = field["value"]
    
    f = passwordResetChangeForm(form_data_dict)

    if f.is_valid():
        
        p = checkValidCode(token)

        if not p:
            return JsonResponse({"status":"error","message":"Valid code not found."}, safe=False)
        else:
            p.user.password = make_password(f.cleaned_data['password1'])
            #p.user.is_active = True

            p.password_reset_key = uuid.uuid4()
            p.email_confirmed = 'yes'
            p.save()
            p.user.save()

            logger.info(f"Reset password for {p}")
        
            return JsonResponse({"status":"success"}, safe=False)
    else:
        logger.info(f"Reset password validation error")
        return JsonResponse({"status":"validation","errors":dict(f.errors.items())}, safe=False)