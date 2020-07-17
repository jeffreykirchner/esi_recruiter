from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django import forms
from main.forms import profileForm
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from main.models import accountTypes,profile

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
   
    #migrate_experiments() #***
    #migrate_locations()
    #migrate_experiments_institutions()
    #migrate_sessions()
    #migrate_majors()

    #migrate_session_users1()
    #migrate_session_users2()  #***
    #migrate_session_users3()  #***

    #migrate_parameters() #***

    token=""
    status="update"            #either filling out the form or 
    if request.method == 'POST':
        form = profileForm(request.POST)        
        
        if form.is_valid():          

            #deactivate user until email is validated
            u = profileCreateUser(form.cleaned_data['email'].lower(),
                                    form.cleaned_data['email'].lower(),
                                    form.cleaned_data['password1'],
                                    form.cleaned_data['first_name'],
                                    form.cleaned_data['last_name'],
                                    form.cleaned_data['chapman_id'],
                                    form.cleaned_data['gender'],
                                    form.cleaned_data['phone'],
                                    form.cleaned_data['major'],
                                    form.cleaned_data['subjectType'],
                                    form.cleaned_data['studentWorker'],
                                    False,
                                    accountTypes.objects.get(id=2))

            profileCreateSendEmail(request,u)
            
            status="done"
            token = u.profile.emailConfirmed

    else:
        form = profileForm()

    return render(request,'profileCreate.html',{'form': form,'status':status,'token':token})    

def profileCreateUser(username,email,password,firstName,lastName,chapmanID,gender,phone,major,subjectType,studentWorker,isActive,accountType):
    logger = logging.getLogger(__name__) 

    u = User.objects.create_user(username = username,
                             email = email,
                             password = password,                                         
                             first_name = firstName,
                             last_name = lastName)

    u.is_active = isActive    
    u.save()

    p = profile(user = u,
                chapmanID = chapmanID,
                gender=gender,
                type=accountType,
                phone=phone,
                major=major,
                subjectType=subjectType,
                studentWorker=studentWorker)

    logger.info("Create Profile: ")
    logger.info(p)

    p.save()
    u.save()

    return u

def profileCreateSendEmail(request,u):
    logger = logging.getLogger(__name__) 
    logger.info("Verify Email: ")
    logger.info(u.profile)

    u.profile.emailConfirmed = get_random_string(length=32)   
    u.profile.save()

    link=request.get_host()      
    link += "/profileVerify/" + u.profile.emailConfirmed +"/"

    msg_html = render_to_string('profileVerifyEmail.html', {'link': link})
    msg_plain = strip_tags(msg_html)
    send_mail(
        'Confirm your email',
        msg_plain,
        settings.DEFAULT_FROM_EMAIL,
        [u.email],
        html_message=msg_html,
        fail_silently=False,
    )