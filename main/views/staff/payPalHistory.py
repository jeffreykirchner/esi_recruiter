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
from django.db.models import OuterRef, Subquery
from django.db.models import Count
from main.models import parameters,help_docs
from datetime import datetime, timedelta,timezone
from main.globals import sendMassEmail

@login_required
@user_is_staff
def payPalHistory(request):
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

        activeCount = User.objects.filter(is_active = True,profile__type__id = 2,profile__email_confirmed = 'yes').count()
        return render(request,'staff/userSearch.html',{"activeCount":activeCount,"helpText":helpText})     

#return list of users based on search criterion
def getHistory(request,data):
    logger = logging.getLogger(__name__)
    logger.info("PayPal History")
    logger.info(data)

    #request.session['userSearchTerm'] = data["searchInfo"]            
    activeOnly = data["activeOnly"] 

    users = lookup(data["searchInfo"],False,activeOnly)            

    errorMessage=""

    if(len(users) >= 1000):
        errorMessage = "Narrow your search"
        users=[]          

    return JsonResponse({"users" : json.dumps(users,cls=DjangoJSONEncoder),"errorMessage":errorMessage},safe=False)

