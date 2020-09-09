from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_subject
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
import logging

@login_required
@user_is_subject
def subjectHome(request,id=None):
    logger = logging.getLogger(__name__) 
   
    
    # logger.info("some info")

    if request.method == 'POST':       

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "action1":
            pass
        elif data["action"] == "action2":
            pass
           
            return JsonResponse({"response" :  "some json"},safe=False)       
    else:      
        return render(request,'subject/home.html',{"u":"" ,"id":""})      