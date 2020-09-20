from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login
from django import forms
from main.forms import verifyForm
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from main.models import profile


#user account info
def profileVerify(request,token):    
    status="update"            #either filling out the form or 
    
    if request.method == 'POST':
        form = verifyForm(request.POST)

        if form.is_valid():          
            try:

                u=User.objects.get(profile__email_confirmed=form.cleaned_data['token'])                
                u.is_active=True
                u.profile.email_confirmed="yes"
                u.profile.paused=False
                u.profile.save()
                u.save()    

                status="done"            
            except ObjectDoesNotExist:
                print("Failed to validate email")
                status ="fail"
    else:
        form = verifyForm(
                initial={'token': token}
            )

    return render(request,'profileVerify.html',{'form':form, 'status':status})    