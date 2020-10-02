from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django import forms
from main.forms import profileForm
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.template.loader import render_to_string
from django.conf import settings
from main.models import account_types,profile
from . import profileCreateSendEmail
from datetime import timedelta

import logging

from main.models.db_migrations import *

#user account info

def profileCreate(request):

    #migrate_institutions()
    #migrate_departments()
    #migrate_accounts()
    #migrate_schools()  #***

    #migrate_subjects1()   #***
    #migrate_subjects2()
   
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

    token=""
    status="update"            #either filling out the form or 
    if request.method == 'POST':
        form = profileForm(request.POST)        
        
        if form.is_valid():          

            #deactivate user until email is validated
            u = profileCreateUser(form.cleaned_data['email'].strip().lower(),
                                    form.cleaned_data['email'].strip().lower(),
                                    form.cleaned_data['password1'],
                                    form.cleaned_data['first_name'].strip().capitalize(),
                                    form.cleaned_data['last_name'].strip().capitalize(),
                                    form.cleaned_data['chapman_id'].strip(),
                                    form.cleaned_data['gender'],
                                    form.cleaned_data['phone'].strip(),
                                    form.cleaned_data['major'],
                                    form.cleaned_data['subject_type'],
                                    form.cleaned_data['studentWorker'],
                                    True,
                                    account_types.objects.get(id=2))

            profileCreateSendEmail(request,u)

            u.profile.setup_email_filter()
            
            status="done"
            token = u.profile.email_confirmed

    else:
        form = profileForm()

    return render(request,'profileCreate.html',{'form': form,'status':status,'token':token})    

def profileCreateUser(username,email,password,firstName,lastName,studentID,gender,phone,major,subject_type,studentWorker,isActive,accountType):
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