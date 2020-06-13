from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.db.models.functions import Lower
from main.forms import userInfoForm
from django.http import Http404
from django.db import IntegrityError
import logging

@login_required
@user_is_staff
def userInfo(request,id=None):
    logger = logging.getLogger(__name__) 
    u=User.objects.get(id=id)
    
    # logger.info(u.ESDU.all())
    # for i in u.ESDU.all():
    #     logger.info(i)

    if request.method == 'POST':       

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "updateUser":
            pass
        elif data["action"] == "getUser":
           
            return JsonResponse({"user" :  u.profile.json()},safe=False)       
    else:      
        return render(request,'staff/userInfo.html',{"u":u,
                                               "experiments":u.ESDU.all() })      

