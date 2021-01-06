from django.shortcuts import render
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.http import Http404
import logging
from main.models import parameters
from main.cron import checkForReminderEmails

def runCronsView(request):
    
    if request.method == 'POST':       

        #data = json.loads(request.body.decode('utf-8'))

        return JsonResponse({"" : ""
                                 },safe=False,
                                )      
                   
    else:     
       logger = logging.getLogger(__name__) 
       logger.info("Run Crons View")
       
       cj = checkForReminderEmails()

       r = cj.do()
       logger.info(r)
       
       status = f'Sent {r}'

       return JsonResponse({"status" : status
                                 },safe=False,
                                )  

    

    