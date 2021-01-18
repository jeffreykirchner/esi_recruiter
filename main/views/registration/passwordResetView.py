from django.shortcuts import redirect

from main.models import parameters
from django.shortcuts import render
import json
from main.forms import passwordResetForm
from django.http import JsonResponse
import logging
from django.contrib.auth.models import User
import uuid
from main.globals import sendMassEmail
from django.db.models.functions import Lower
from django.urls import reverse
from django.contrib.auth import logout

def passwordResetView(request):

    logger = logging.getLogger(__name__) 
    
    #logger.info(request)
    
    if request.method == 'POST':

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "send_reset":
            return send_reset(request,data)

        return JsonResponse({"response" :  "error"},safe=False)

    else:
        logout(request)

        p = parameters.objects.first()
        labManager = p.labManager 

        form = passwordResetForm()

        form_ids=[]
        for i in form:
            form_ids.append(i.html_name)

        return render(request,'registration/passwordReset.html',{"labManager":labManager,
                                                         "form":form,
                                                         "form_ids":form_ids})
    
def send_reset(request,data):
    logger = logging.getLogger(__name__) 
   
    p = parameters.objects.first()

    #convert form into dictionary
    form_data_dict = {}             

    for field in data["formData"]:            
        form_data_dict[field["name"]] = field["value"]
    
    f = passwordResetForm(form_data_dict)

    if f.is_valid():

        username = f.cleaned_data['username']
        
        u = User.objects.filter(email = username.lower())

        logger.info(u)

        if u.count() != 1:
            logger.info(f"passwordResetView user not found {username}")
            return JsonResponse({"status":"error","message":"Account not found."}, safe=False)
        else:
            u = u.first()
            u.profile.password_reset_key = uuid.uuid4()
            u.profile.save()

            emailList = [{"email":u.email,"first_name":u.first_name}]
            subjectText = p.passwordResetTextSubject
            messageText = p.passwordResetText
            messageText = messageText.replace("[email]",u.email)
            messageText = messageText.replace("[reset link]",p.siteURL + reverse('passwordResetChange',args=(u.profile.password_reset_key,)))
            messageText = messageText.replace("[contact email]",p.labManager.email)

            mailResult = sendMassEmail(emailList,subjectText, messageText)

            if mailResult.get("mailCount",-1)>0:
                logger.info(f"Reset password for {username}")
                return JsonResponse({"status":"success"}, safe=False)                
            else:
                logger.info(f"Reset password failed for {username} : {mailResult}")
                return JsonResponse({"status":"error","message":"There was a problem sending the email.  Please try again."}, safe=False)
    
    else:
        logger.info(f"send_reset Reset password validation error")
        return JsonResponse({"status":"validation","errors":dict(f.errors.items())}, safe=False)