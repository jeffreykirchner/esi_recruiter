from django.contrib.auth import authenticate, login
from django.shortcuts import redirect

from main.models import Front_page_notice,parameters,Front_page_notice
from django.shortcuts import render
import json
from main.forms import loginForm
from django.http import JsonResponse
import logging

def loginView(request):

    logger = logging.getLogger(__name__) 
    
    #logger.info(request)
    
    if request.method == 'POST':

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "login":
            return login_function(request,data)

        return JsonResponse({"response" :  "error"},safe=False)

    else:
        p = parameters.objects.first()
        labManager = p.labManager 

        form = loginForm()

        form_ids=[]
        for i in form:
            form_ids.append(i.html_name)

        fpn_list = Front_page_notice.objects.filter(enabled = True)

        return render(request,'registration/login.html',{"labManager":labManager,
                                                         "form":form,
                                                         "fpn_list":fpn_list,
                                                         "form_ids":form_ids})
    
def login_function(request,data):
    logger = logging.getLogger(__name__) 
    #logger.info(data)

    #convert form into dictionary
    form_data_dict = {}             

    for field in data["formData"]:            
        form_data_dict[field["name"]] = field["value"]
    
    f = loginForm(form_data_dict)

    if f.is_valid():

        username = f.cleaned_data['username']
        password = f.cleaned_data['password']

        logger.info(f"Login user {username}")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            logger.info(f"Login user {username} success")

            return JsonResponse({"status":"success"}, safe=False)
        else:
            logger.info(f"Login user {username} fail user / pass")
            
            return JsonResponse({"status":"error"}, safe=False)
    else:
        logger.info(f"Login user {username} validation error")
        return JsonResponse({"status":"validation","errors":dict(form.errors.items())}, safe=False)