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

def passwordResetChangeView(request):

    logger = logging.getLogger(__name__) 
    
    #logger.info(request)
    
    if request.method == 'POST':

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "send_reset":
            return send_reset(request,data)

        return JsonResponse({"response" :  "error"},safe=False)

    else:

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

        if u.count() != 1:
            return JsonResponse({"status":"error","message":"Account not found."}, safe=False)
        else:
            u = u.first()
            u.profile.password_reset_key = uuid.uuid4()
            u.profile.save()

            emailList = [{"email":u.email,"first_name":u.first_name}]
            subjectText = p.passwordResetTextSubject
            messageText = p.passwordResetText
            messageText = messageText.replace("[email]",u.email)
            messageText = messageText.replace("[reset link]",p.siteURL + reverse('passwordReset') +  str(u.profile.password_reset_key))
            messageText = messageText.replace("[contact email]",p.labManager.email)

            mailResult = sendMassEmail(emailList,subjectText, messageText)


        logger.info(f"Reset password for {username}")
        
        return JsonResponse({"status":"error"}, safe=False)
    else:
        logger.info(f"Reset password validation error {data}")
        return JsonResponse({"status":"validation","errors":dict(f.errors.items())}, safe=False)