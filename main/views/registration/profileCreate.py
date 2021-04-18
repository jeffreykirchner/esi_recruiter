from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login,logout
from main.forms import profileForm
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.template.loader import render_to_string
from django.conf import settings
from main.models import account_types,profile,help_docs
from main.views import profile_create_send_email
from datetime import timedelta
from django.db.models import CharField,Q,F,Value as V
from django.urls import reverse
from django.http import JsonResponse
import json

import logging

from main.models.db_migrations import *

#user account info

def profileCreate(request):
    logger = logging.getLogger(__name__) 

    #migrate_institutions()
    #migrate_departments()
    #migrate_accounts()
    #migrate_traits()
    
    #migrate_schools()  #***

    #migrate_subjects1()   #***
    #migrate_subjects2()
    #migrate_profile_traits() #***
   
    #migrate_experiments()
    #migrate_recruitment_parameters() #***
    #migrate_locations()
    #migrate_experiments_institutions()
    #migrate_sessions()
    #migrate_majors()

    #migrate_session_users1()
    #migrate_session_users2()  #***
    #migrate_session_users4()  #***
    #migrate_session_users3()  #***

    #migrate_parameters() #***
    #migrate_faqs() #****


    if request.method == 'POST':
        
        #check that request id json formatted
        try:
            request_body = None
            request_body = request.body.decode('utf-8')
            data = json.loads(request_body)
        except Exception  as e:  
           logger.warning(f"Profile create post json error: {request_body}, Exception: {e}") 
           return JsonResponse({"status" :  "error"},safe=False)

        #check for correct action
        action = data.get("action", "fail")

        if action == "create":
            return createUser(request,data)

        #valid action not found
        logger.warning(f"Profile create post error: {data}")
        return JsonResponse({"status" :  "error"},safe=False)           

    else:
        logout(request)
        
        form = profileForm()

        #logger.info(reverse('profile'))
        try:
            helpText = help_docs.objects.annotate(rp = V(reverse('profile'),output_field=CharField()))\
                                        .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
            helpText = "No help doc was found."

        form_ids=[]
        for i in form:
            form_ids.append(i.html_name)

        return render(request,'registration/profileCreate.html',{'form': form,
                                                                 'helpText':helpText,
                                                                 'form_ids':form_ids})    

def createUser(request,data):
    logger = logging.getLogger(__name__) 
    logger.info("Create User")

    form_data_dict = {}             

    for field in data["formData"]:            
        form_data_dict[field["name"]] = field["value"]

        #remove caps from email form
        if field["name"] == "email":
            form_data_dict["email"] = form_data_dict["email"].strip().lower()

    
    f = profileForm(form_data_dict)

    if f.is_valid():
        
        u = profileCreateUser(f.cleaned_data['email'].strip().lower(),
                                    f.cleaned_data['email'].strip().lower(),
                                    f.cleaned_data['password1'],
                                    f.cleaned_data['first_name'].strip().capitalize(),
                                    f.cleaned_data['last_name'].strip().capitalize(),
                                    f.cleaned_data['chapman_id'].strip(),
                                    f.cleaned_data['gender'],
                                    f.cleaned_data['phone'].strip(),
                                    f.cleaned_data['major'],
                                    f.cleaned_data['subject_type'],
                                    f.cleaned_data['studentWorker'],
                                    True,
                                    account_types.objects.get(id=2))

        profile_create_send_email(request,u)

        u.profile.setup_email_filter()

        #log new user in
        #user = authenticate(request, username=u.username, password=u.password)
        login(request, u) 
         
        return JsonResponse({"status":"success"}, safe=False)

    else:
        logger.info(f"createUser validation error")
        return JsonResponse({"status":"error","errors":dict(f.errors.items())}, safe=False)


def profileCreateUser(username, email, password, firstName, lastName, studentID, 
                      gender, phone, major, subject_type, studentWorker, isActive, 
                      accountType):

    logger = logging.getLogger(__name__) 

    u = User.objects.create_user(username = username,
                                 email = email,
                                 password = password,                                         
                                 first_name = firstName,
                                 last_name = lastName)

    u.is_active = isActive    
    u.save()

    p = profile(user = u,
                studentID = studentID,
                gender=gender,
                type=accountType,
                phone=phone,
                major=major,
                subject_type=subject_type,
                studentWorker=studentWorker)

    logger.info("Create Profile: ")
    logger.info(p)

    p.save()
    u.save()

    return u