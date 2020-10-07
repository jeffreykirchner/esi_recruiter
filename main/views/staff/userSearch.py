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
from . import sendMassEmail

@login_required
@user_is_staff
def userSearch(request):
    if request.method == 'POST':

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getUsers":
            return getUsers(request,data)
        elif data["action"] == "getBlackBalls":
            return getBlackBalls(request,data)
        elif data["action"] == "getNoShows":
            return getNoShows(request,data)
        elif data["action"] == "sendEmail":
            return sendEmail(request,data)

    else:
        try:
            helpText = help_docs.objects.annotate(rp = V(request.path,output_field=CharField()))\
                                    .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
             helpText = "No help doc was found."

        activeCount = User.objects.filter(is_active = True,profile__type__id = 2,profile__email_confirmed = 'yes').count()
        return render(request,'staff/userSearch.html',{"activeCount":activeCount,"helpText":helpText})     

#send an email to active users
def sendEmail(request,data):
    logger = logging.getLogger(__name__)
    logger.info("Send message to all active users")
    logger.info(data)

    if request.user.is_superuser:

        subjectText =  data["subject"]
        messageText = data["text"]

        users_list = User.objects.filter(is_active = True, profile__email_confirmed = 'yes',profile__type__id = 2)

        emailList = []
        
        for i in users_list:
            emailList.append({"email":i.email,"first_name":i.first_name})        

        mailResult = sendMassEmail(emailList,subjectText, messageText)

        logger.info(emailList)
    else:
        logger.info("Send message to all active users error, not super user : user " + str(request.user.id))
        mailResult = {"mailCount":0,"errorMessage":"You are not an elevated user."}

    return JsonResponse({"mailResult":mailResult}, safe=False)

#get a list of no show violators
def getNoShows(request,data):
    logger = logging.getLogger(__name__)
    logger.info("Get no show blocks")
    logger.info(data)

    p = parameters.objects.first()
    d = datetime.now(timezone.utc) - timedelta(days=p.noShowCutoffWindow)

    errorMessage = ""
    activeOnly = data["activeOnly"] 

    users=User.objects.order_by(Lower('last_name'),Lower('first_name')) \
                .filter(Q(ESDU__confirmed = True) &
                    Q(ESDU__attended = False) &
                    Q(ESDU__bumped = False) & 
                    Q(ESDU__experiment_session_day__experiment_session__canceled = False) &
                    Q(ESDU__experiment_session_day__date__gte = d))\
                .annotate(noShows = Count('id'))\
                .filter(noShows__gte = p.noShowCutoff)\
                .values("id","first_name","last_name","email","profile__studentID","profile__type__name","is_active","profile__blackballed")

    #logger.info(users.query)

    if activeOnly:
        users = users.filter(is_active = True)

    u_list = list(users)

    return JsonResponse({"users" :  json.dumps(u_list,cls=DjangoJSONEncoder),"errorMessage":errorMessage},safe=False)

#get a list of all active black ball users
def getBlackBalls(request,data):
    logger = logging.getLogger(__name__)
    logger.info("Black Balls")
    logger.info(data)

    errorMessage=""
    activeOnly = data["activeOnly"] 

    users=User.objects.order_by(Lower('last_name'),Lower('first_name')) \
                .filter(profile__blackballed=True) \
                .select_related('profile') \
                .values("id","first_name","last_name","email","profile__studentID","profile__type__name","is_active","profile__blackballed")
    
    if activeOnly:
        users = users.filter(is_active = True)

    u_list = list(users)

    return JsonResponse({"users" :  json.dumps(u_list,cls=DjangoJSONEncoder),"errorMessage":errorMessage},safe=False)

#return list of users based on search criterion
def getUsers(request,data):
    logger = logging.getLogger(__name__)
    logger.info("User Search")
    logger.info(data)

    #request.session['userSearchTerm'] = data["searchInfo"]            
    activeOnly = data["activeOnly"] 

    users = lookup(data["searchInfo"],False,activeOnly)            

    errorMessage=""

    if(len(users) >= 1000):
        errorMessage = "Narrow your search"
        users=[]          

    return JsonResponse({"users" : json.dumps(users,cls=DjangoJSONEncoder),"errorMessage":errorMessage},safe=False)

#search for users that back search criterion
def lookup(value,returnJSON,activeOnly):
    logger = logging.getLogger(__name__)
    logger.info("User Lookup")
    logger.info(value)

    value = value.strip()

    users=User.objects.order_by(Lower('last_name'),Lower('first_name')) \
                      .filter(Q(last_name__icontains = value) |
                              Q(first_name__icontains = value) |
                              Q(email__icontains = value) |
                              Q(profile__studentID__icontains = value) |
                              Q(profile__type__name__icontains = value))\
                      .select_related('profile')\
                      .values("id","first_name","last_name","email","profile__studentID","profile__type__name","is_active","profile__blackballed")


    if activeOnly:
        users = users.filter(is_active = True, profile__email_confirmed = 'yes')

    u_list = list(users)

    logger.info(str(len(u_list)) + " results found.")

    for u in u_list:
        u['first_name'] = u['first_name'].capitalize()
        u['last_name'] = u['last_name'].capitalize()

    if returnJSON:
        #print(json.dumps(list(users),cls=DjangoJSONEncoder))
        return json.dumps(u_list,cls=DjangoJSONEncoder)
    else:
        return u_list
