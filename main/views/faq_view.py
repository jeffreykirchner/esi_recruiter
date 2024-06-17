import json
import logging

from django.shortcuts import render
from django.http import JsonResponse

from main.models import FAQ
from main.models import parameters

from django.views import View

class FaqView(View):
    '''
    FAQ view
    '''

    template_name = "subject/faq.html"

    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logger = logging.getLogger(__name__)

        p = parameters.objects.first()
        labManager = p.labManager      
        
        return render(request, self.template_name, {"labManager":labManager}) 
    
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__) 

        data = json.loads(request.body.decode('utf-8'))

        action = data.get("status","fail")

        if action == "getFaqs":
            return getFaqs(data)       
        
        #no valid action found
        logger.info(f"FAQ Post error: {data}")
        return JsonResponse({"status" :  "error"},safe=False)

#get the session and notes subject has participated in
def getFaqs(data):
    logger = logging.getLogger(__name__) 
    logger.info(f"Get faqs: {data}")

    return JsonResponse({"faq" : [i.json() for i in FAQ.objects.filter(active = True)]
                                 },safe=False,
                                )