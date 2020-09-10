from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_subject
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
import logging
from main.models import experiment_session_day_users

@login_required
@user_is_subject
def subjectHome(request):
    logger = logging.getLogger(__name__) 
   
    
    # logger.info("some info")

    if request.method == 'POST':     

        #u=request.user  
        u=User.objects.get(id=11330)

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getCurrentInvitations":
            return getCurrentInvitations(data,u)
        elif data["action"] == "acceptInvitation":
            return acceptInvitation(data,u)
        elif data["action"] == "cancelAcceptInvitation":
            return cancelAcceptInvitation(data,u)
        elif data["action"] == "showAllInvitations":
            return showAllInvitations(data,u)
           
        return JsonResponse({"response" :  "fail"},safe=False)       
    else:      
        return render(request,'subject/home.html',{"u":"" ,"id":""})      

#return invitations for subject
def getCurrentInvitations(data,u):    
    logger = logging.getLogger(__name__)
    logger.info("Get current invitations")    
    logger.info(data)

    upcomingInvitations = u.profile.sorted_session_list_upcoming()
    pastAcceptedInvitations = u.profile.sorted_session_day_list_earningsOnly()

    return JsonResponse({"upcomingInvitations" : upcomingInvitations,"pastAcceptedInvitations":pastAcceptedInvitations}, safe=False)

#subject has accepted an invitation
def acceptInvitation(data,u):    
    logger = logging.getLogger(__name__)
    logger.info("Accept invitation")    
    logger.info(data)

    es_id = data["id"]

    try:
        qs = u.profile.sessions_upcoming()
        qs = qs.filter(id = es_id).first()

        if qs:

            experiment_session_day_users.objects.filter(experiment_session_day__experiment_session__id = qs.id,
                                                user__id=u.id)\
                                        .update(confirmed=True)  

        else:
            logger.info("Invitation not found")             
            logger.info("User: " + str(u.id))

    except:
        logger.info("Accept invitation error")             
        logger.info("User: " + str(u.id))    

    upcomingInvitations = u.profile.sorted_session_list_upcoming()

    return JsonResponse({"upcomingInvitations" : upcomingInvitations}, safe=False)

#return invitations for subject
def cancelAcceptInvitation(data,u):    
    logger = logging.getLogger(__name__)
    logger.info("Cancel accept invitation")    
    logger.info(data)

    es_id = data["id"]

    try:
        qs = u.profile.sessions_upcoming()
        qs = qs.filter(id = es_id).first()

        if qs:
            if qs.hoursUntilFirstStart()>24:
                experiment_session_day_users.objects.filter(experiment_session_day__experiment_session__id = qs.id,
                                                user__id=u.id)\
                                        .update(confirmed=False)
        else:
            logger.info("Invitation not found")             
            logger.info("User: " + str(u.id))

    except:
        logger.info("Cancel invitation error")             
        logger.info("User: " + str(u.id))    

    upcomingInvitations=u.profile.sorted_session_list_upcoming()

    return JsonResponse({"upcomingInvitations" : upcomingInvitations}, safe=False)

#return list of past declined invitations
def showAllInvitations(data,u):    
    logger = logging.getLogger(__name__)
    logger.info("Show all invitations")    
    logger.info(data)

    allInvitations = u.profile.sorted_session_day_list_full()

    return JsonResponse({"allInvitations" : allInvitations}, safe=False)