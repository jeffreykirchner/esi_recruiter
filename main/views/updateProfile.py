from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from main.forms import profileFormUpdate
from . import profileCreateSendEmail

from django.conf import settings

import requests
import logging

#user account info
@login_required
def updateProfile(request):
    logger = logging.getLogger(__name__)     

    try:
        status="update"            #either filling out the form or 
        emailVerificationRequired=False
        u=request.user
        
        if request.method == 'POST':
            form = profileFormUpdate(request.POST,user=request.user)

            #print(request.POST)

            if form.is_valid():                         

                if u.email != form.cleaned_data['email'].lower():
                    emailVerificationRequired=True
                
                u.first_name=form.cleaned_data['first_name'].strip().capitalize()
                u.last_name=form.cleaned_data['last_name'].strip().capitalize()
                u.email=form.cleaned_data['email'].strip().lower()
                u.username=u.email

                u.profile.chapmanID=form.cleaned_data['chapman_id'].strip()
                u.profile.gender=form.cleaned_data['gender']
                u.profile.subjecType = form.cleaned_data['subjectType']
                u.profile.studentWorker = form.cleaned_data['studentWorker']
                u.profile.phone = form.cleaned_data['phone'].strip()
                u.profile.major = form.cleaned_data['major']

                if form.cleaned_data['password1']:
                    if form.cleaned_data['password1'] != "":               
                        u.set_password(form.cleaned_data['password1'])                    

                if emailVerificationRequired:
                    #u.is_active=False     
                    u.profile.emailConfirmed="no"                           
                    profileCreateSendEmail(request,u)

                u.save()
                u.profile.save()
                u.profile.setupEmailFilter()
                status="done"
        else:
            logger.info("show profile")

            form = profileFormUpdate(
                initial={'first_name': request.user.first_name,
                         'last_name': request.user.last_name,
                         'chapman_id': request.user.profile.chapmanID,
                         'email':request.user.email,
                         'gender':request.user.profile.gender.id,
                         'phone':request.user.profile.phone,
                         'major':request.user.profile.major.id,
                         'subjectType':request.user.profile.subjectType.id,
                         'studentWorker':"Yes" if request.user.profile.studentWorker else "No"}
            )

    except u.DoesNotExist:
        raise Http404('Profile not found')

    return render(request,'profile.html',{'form': form,
                                          'status':status,
                                          'emailVerificationRequired':emailVerificationRequired})    



