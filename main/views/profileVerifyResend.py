from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login
from django import forms
from main.forms import verifyFormResend
from .profileCreate import profileCreateSendEmail
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from main.models import profile


#user account info
def profileVerifyResend(request,token):    
    status="update"            #either filling out the form or 
    
    if request.method == 'POST':
        form = verifyFormResend(request.POST)
        status = "fail"
        if form.is_valid():          
            
                
                try:
                    #look for token first
                    u=User.objects.get(profile__emailConfirmed=form.cleaned_data['token'])    
                    u.email = form.cleaned_data['email']
                    u.username = form.cleaned_data['email']
                    u.save()
                    status="done"             
                except ObjectDoesNotExist:
                    try:
                        u=User.objects.get(email=form.cleaned_data['email']) 
                        status="done"
                    except ObjectDoesNotExist:
                        status="fail"                    

                if status != "fail":
                    profileCreateSendEmail(request,u)                    

            #
             #   print("Failed to validate email")
             #   status ="fail"
    else:
        form = verifyFormResend(
                initial={'token': token}
            )

    return render(request,'profileVerifyResend.html',{'form':form, 'status':status})    