import json
import uuid
import logging

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.auth import logout
from django.views import View

from main.models import Parameters
from main.globals import send_mass_email_service
from main.forms import passwordResetForm

class PasswordResetView(View):
    '''
    password reset view
    '''

    template_name = "registration/password_reset.html"

    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logout(request)

        p = Parameters.objects.first()
        labManager = p.labManager 

        form = passwordResetForm()

        form_ids=[]
        for i in form:
            form_ids.append(i.html_name)

        return render(request,self.template_name,{"labManager":labManager,
                                                  "form":form,
                                                  "form_ids":form_ids})
    

    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "send_reset":
            return send_reset(request,data)

        return JsonResponse({"response" :  "error"},safe=False)

def send_reset(request, data):
    logger = logging.getLogger(__name__) 
   
    params = Parameters.objects.first()

    #convert form into dictionary
    form_data_dict = data["formData"]             

    # for field in data["formData"]:            
    #     form_data_dict[field["name"]] = field["value"]
    
    form = passwordResetForm(form_data_dict)

    if form.is_valid():

        username = form.cleaned_data['username']
        
        user_list = User.objects.filter(email=username.lower())

        #logger.info(user_list)

        if user_list.count() != 1:
            logger.info(f"passwordResetView user not found {username}")
            return JsonResponse({"status":"error", "message":"Account not found."}, safe=False)
        else:
            user = user_list.first()
            user.profile.password_reset_key = uuid.uuid4()
            user.profile.save()

            user_list = [{"email" : user.email,
                         "variables": [{"name":"first name", "text" : user.first_name},
                                       {"name":"email", "text" : user.email},
                                       {"name":"reset link", "text" : params.siteURL + reverse('passwordResetChange', args=(user.profile.password_reset_key,))},
                                       {"name":"contact email", "text" : params.labManager.email}]}]

            memo = f"Password reset for: {user}"

            mail_result = send_mass_email_service(user_list, params.passwordResetTextSubject, params.passwordResetText, params.passwordResetText, memo, 5)

            if mail_result.get("mail_count", -1) > 0:
                logger.info(f"Reset password for {username}")
                return JsonResponse({"status":"success"}, safe=False)                
            
            logger.info(f"Reset password failed for {username} : {mail_result}")
            return JsonResponse({"status":"error", "message":"There was a problem sending the email.  Please try again."}, safe=False)
    
    else:
        logger.info(f"send_reset Reset password validation error")
        return JsonResponse({"status":"validation", "errors":dict(form.errors.items())}, safe=False)