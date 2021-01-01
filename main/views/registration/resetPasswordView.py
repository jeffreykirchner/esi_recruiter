from django.contrib.auth import authenticate, login

from main.models import Front_page_notice,parameters
from django.shortcuts import render
import json

def resetPasswordView(request):
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to a success page.
            ...
        else:
            # Return an 'invalid login' error message.
            ...
    else:
        p = parameters.objects.first()
        labManager = p.labManager 

        return render(request,'registration/login.html',{"labManager":labManager})