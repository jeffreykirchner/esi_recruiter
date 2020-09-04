from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
import logging
from main.forms import pettyCashForm

@login_required
@user_is_staff
def reportsView(request):
    logger = logging.getLogger(__name__) 
    

    if request.method == 'POST':       

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "pettyCash":
            return pettyCash(data)
        elif data["action"] == "action2":
            pass
           
        return JsonResponse({"response" :  "fail"},safe=False)       
    else:      

        return render(request,'staff/reports.html',{"pettyCashForm":pettyCashForm() ,
                                                    "id":""})      

def pettyCash(data):
    return JsonResponse({"response" :  "some json"},safe=False)