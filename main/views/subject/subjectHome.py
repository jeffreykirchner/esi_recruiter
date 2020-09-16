from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_subject
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
import logging
from main.models import experiment_session_day_users,parameters
from datetime import datetime, timedelta,timezone
import pytz
from django.db.models import Q

@login_required
@user_is_subject
def subjectHome(request):
    logger = logging.getLogger(__name__) 
   
    
    # logger.info("some info")

    if request.method == 'POST':     

        u=request.user  
        #u=User.objects.get(id=11330)  #tester

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
        p = parameters.objects.get(id=1)

        labManager = p.labManager
        return render(request,'subject/home.html',{"labManager":labManager})      

#return invitations for subject
def getCurrentInvitations(data,u):    
    logger = logging.getLogger(__name__)
    logger.info("Get current invitations")    
    logger.info(data)

    failed=False

    upcomingInvitations = u.profile.sorted_session_list_upcoming()
    pastAcceptedInvitations = u.profile.sorted_session_day_list_earningsOnly()

    return JsonResponse({"upcomingInvitations" : upcomingInvitations,"pastAcceptedInvitations":pastAcceptedInvitations,"failed":failed}, safe=False)

#subject has accepted an invitation
def acceptInvitation(data,u):    
    logger = logging.getLogger(__name__)
    logger.info("Accept invitation")    
    logger.info(data)

    es_id = data["id"]

    # try:
    qs = u.profile.sessions_upcoming(False,datetime.now(pytz.utc) - timedelta(hours=1))
    qs = qs.filter(id = es_id).first()                               #session being accepted

    failed=False

    if qs:

        #check that session has not started
        if qs.hoursUntilFirstStart() <= -0.25:
            logger.info("Invitation failed session started")             
            logger.info("User: " + str(u.id))

            failed=True

        #check session not already full
        if qs.getFull(): 
            logger.info("Invitation failed accept session full")             
            logger.info("User: " + str(u.id))
            failed=True
        
        #check user is not already attending a recruitment violation
        if not failed:
            user_list_valid = qs.getValidUserList([{'id':u.id}],False,0)

            if not u in user_list_valid:
                logger.info("Invitation failed recruitment violation")             
                logger.info("User: " + str(u.id))
                failed=True
        
        #check that by attending this experiment, user will not create recruitment violation in another confirmed experiment
        if not failed:
            qs_attending = u.profile.sessions_upcoming(True,qs.getFirstDate())

            for s in qs_attending:
                user_list_valid = s.getValidUserList([{'id':u.id}],False,qs.experiment.id)

                if not u in user_list_valid:
                    logger.info("Invitation failed attended recruitment violation")             
                    logger.info("User: " + str(u.id) + ", attending session: " + str(s.id) + " , violation experiment: " + str(qs.experiment.id) )
                    failed=True
                    break

        #do a backup check that user has not already done this experiment, if prohibited
        if not failed:
            esdu = experiment_session_day_users.objects.filter(experiment_session_day__experiment_session__id = qs.id,
                                            user__id=u.id).first()
            
            if esdu.getAlreadyAttended():
                logger.info("Invitation failed, user has already done this experiment")
                logger.info("User: " + str(u.id) + ", attending session: " + str(esdu.id))
                failed=True
        
        #update confirmed status
        if not failed:
            logger.info("Accept Not Failed")
            experiment_session_day_users.objects.filter(experiment_session_day__experiment_session__id = qs.id,
                                            user__id=u.id)\
                                    .update(confirmed=True)
        else:
            logger.info("Accept Failed") 

    else:
        logger.info("Invitation not found")             
        logger.info("User: " + str(u.id))
        failed=True

    # except Exception  as e:
    #     logger.info("Accept invitation error")             
    #     logger.info("User: " + str(u.id))    
    #     logger.info(e)

    upcomingInvitations = u.profile.sorted_session_list_upcoming()

    return JsonResponse({"upcomingInvitations" : upcomingInvitations,"failed":failed}, safe=False)

#return invitations for subject
def cancelAcceptInvitation(data,u):    
    logger = logging.getLogger(__name__)
    logger.info("Cancel accept invitation")    
    logger.info(data)

    es_id = data["id"]

    failed=False

    try:
        qs = u.profile.sessions_upcoming(False,datetime.now(pytz.utc) - timedelta(hours=1))
        qs = qs.filter(id = es_id).first()
        
        if qs:
            #subject cannot cancel within 24 hours of an experiment
            if qs.hoursUntilFirstStart() < 24:
                logger.info("Invitation failed cancel within 24 hours")             
                logger.info("User: " + str(u.id) + " Session: " + str(qs.id))
                failed=True

            #subjects cannot cancel if they have been marked as bumped or attended
            if not failed:
                esdu_list = experiment_session_day_users.objects\
                                       .filter(experiment_session_day__experiment_session__id = qs.id,
                                               user__id=u.id)\
                                       .filter(Q(attended=True) | Q(bumped=True))
                
                if esdu_list:
                    logger.info("Invitation failed allready attending or bumped")             
                    logger.info("User: " + str(u.id) + " Session: " + str(qs.id))
                    failed=True

                  
            if not failed:
                logger.info("Cancel Not Failed")
                experiment_session_day_users.objects.filter(experiment_session_day__experiment_session__id = qs.id,
                                                user__id=u.id)\
                                        .update(confirmed=False)
            else:
                logger.info("Cancel Accept Failed") 
        else:
            logger.info("Invitation not found")             
            logger.info("User: " + str(u.id))
            failed=True

    except Exception  as e:
        logger.info("Cancel invitation error")             
        logger.info("User: " + str(u.id))    
        logger.info(e)

    upcomingInvitations=u.profile.sorted_session_list_upcoming()

    return JsonResponse({"upcomingInvitations" : upcomingInvitations,"failed":failed}, safe=False)

#return list of past declined invitations
def showAllInvitations(data,u):    
    logger = logging.getLogger(__name__)
    logger.info("Show all invitations")    
    logger.info(data)

    allInvitations = u.profile.sorted_session_day_list_full()

    return JsonResponse({"allInvitations" : allInvitations}, safe=False)