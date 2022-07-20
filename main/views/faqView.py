import json
import logging

from django.shortcuts import render
from django.http import JsonResponse

from main.models import faq
from main.models import parameters

def faqView(request):
    logger = logging.getLogger(__name__) 

    if request.method == 'POST':       

        data = json.loads(request.body.decode('utf-8'))

        action = data.get("status","fail")

        if action == "getFaqs":
            return getFaqs(data)       
        
        #no valid action found
        logger.info(f"FAQ Post error: {data}")
        return JsonResponse({"status" :  "error"},safe=False)
                   
    else:     

        p = parameters.objects.first()
        labManager = p.labManager      
        
        return render(request,'subject/faq.html',{"labManager":labManager})  

#get the session and notes subject has participated in
def getFaqs(data):
    logger = logging.getLogger(__name__) 
    logger.info(f"Get faqs: {data}")

    return JsonResponse({"faq" : [i.json() for i in faq.objects.filter(active = True)]
                                 },safe=False,
                                )