from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import CharField,Q,F,Value as V
from django.db.models.functions import Lower,Concat
from django.urls import reverse
from main import views
import logging
from main.models import parameters,help_docs
from datetime import datetime, timedelta,timezone
from django.conf import settings
import requests

@login_required
@user_is_staff
def PayPalHistory(request):
    if request.method == 'POST':

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getHistory":
            return getHistory(request,data)        

    else:
        try:
            helpText = help_docs.objects.annotate(rp = V(request.path,output_field=CharField()))\
                                    .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
             helpText = "No help doc was found."

        
        return render(request,'staff/payPalHistory.html',{"helpText":helpText})     

#return list of users based on search criterion
def getHistory(request,data):
    logger = logging.getLogger(__name__)
    logger.info("PayPal History")
    logger.info(data)

    #request.session['userSearchTerm'] = data["searchInfo"]            
    history=[]    
    errorMessage=""      

    # headers = {'WWW-Authenticate': f'{settings.PPMS_USER_NAME} : {settings.PPMS_PASSWORD}',
    #            'Content-Type' : 'application/json'}
            
    # data = {}    
    
    try:

        r = requests.get(f'{settings.PPMS_HOST}/payments/',
                     auth=(str(settings.PPMS_USER_NAME), str(settings.PPMS_PASSWORD)))

        #logger.info(r.status_code)

        if r.status_code != 200:
            errorMessage=r.json().get("detail")
        else:
            history = r.json()

    except Exception  as e: 
            logger.warning(f'PayPalHistory Error: {e}')
            errorMessage = "Unable to retrieve history."

    return JsonResponse({"history" : history,"errorMessage":errorMessage},safe=False)


