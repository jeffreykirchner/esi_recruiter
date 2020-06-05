from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django import forms
from .forms import profileForm
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from main.models import accountTypes

import logging

#user account info

def profileCreate(request):

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
                                    False,
                                    False,
                                    True,
                                    accountTypes.objects.get(id=2))

            profileCreateSendEmail(request,u)
            
            status="done"
            token = u.profile.emailConfirmed

    else:
        form = profileForm()

    return render(request,'profileCreate.html',{'form': form,'status':status,'token':token})    

def profileCreateUser(username,email,password,firstName,lastName,chapmanID,gender,labUser,isActive,saveUser,accountType):
    u = User.objects.create_user(username = username,
                             email = email,
                             password = password,                                         
                             first_name = firstName,
                             last_name = lastName)
            
    u.profile.chapmanID = chapmanID
    u.profile.gender =  gender
    u.profile.labUser = labUser
    u.is_active = isActive
    u.type = accountType                                      
    
    if saveUser:
        u.save()

    return u

def profileCreateSendEmail(request,u):
    u.profile.emailConfirmed = get_random_string(length=32)   
    u.save()

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