from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.http import Http404
import logging
from main.models import faq,parameters

def faqView(request):

    if request.method == 'POST':       

        data = json.loads(request.body.decode('utf-8'))

        if data["status"] == "getFaqs":
            return getFaqs(data)       
                   
    else:     

        p = parameters.objects.first()
        labManager = p.labManager      
        
        return render(request,'subject/faq.html',{"labManager":labManager})  

#get the session and notes subject has participated in
def getFaqs(data):
    logger = logging.getLogger(__name__) 
    logger.info("Get faqs")
    logger.info(data)

    

    return JsonResponse({"faq" : [i.json() for i in faq.objects.filter(active = True)]
                                 },safe=False,
                                )