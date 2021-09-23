import json
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.http import HttpResponse
from django.shortcuts import redirect

from main.decorators import user_is_staff

@login_required
@user_is_staff
@staff_member_required

def SubjectAutoLogin(request, id=None):
    logger = logging.getLogger(__name__) 
    
    
    # logger.info("some info")

    if request.method == 'POST':       

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "action1":
            pass
        elif data["action"] == "action2":
            pass
           
        return JsonResponse({"response" :  "error"}, safe=False)       
    else:   
        try:
            user = User.objects.get(id=id)
        except Exception  as e:             
           return HttpResponse('User not found', content_type="text/plain")

        logout(request)
        login(request, user)

        return redirect('mainHome')