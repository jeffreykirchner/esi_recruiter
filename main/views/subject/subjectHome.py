from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_subject,email_confirmed
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
import logging
from main.models import experiment_session_day_users,parameters,help_docs
from datetime import datetime, timedelta,timezone
import pytz
from django.db.models import CharField,Q,F,Value as V

@login_required
@user_is_subject
@email_confirmed
def subjectHome(request):
    logger = logging.getLogger(__name__) 
   
    
    # logger.info("some info")
    u=request.user  

    if request.method == 'POST':     

       
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
        elif data["action"] == "acceptConsentForm":
            return acceptConsentForm(data,u)
           
        return JsonResponse({"response" :  "fail"},safe=False)       
    else:      
        p = parameters.objects.first()

        labManager = p.labManager

        try:
            helpText = help_docs.objects.annotate(rp = V(request.path,output_field=CharField()))\
                                    .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
            helpText = "No help doc was found."
        
        return render(request,'subject/home.html',{"labManager":labManager,
                                                   "helpText":helpText})      

#return invitations for subject
def getCurrentInvitations(data,u):    
    logger = logging.getLogger(__name__)
    logger.info("Get current invitations")    
    logger.info(data)

    p = parameters.objects.first()

    failed=False

    upcomingInvitations = u.profile.sorted_session_list_upcoming()
    pastAcceptedInvitations = u.profile.sorted_session_day_list_earningsOnly()
    consent_required = u.profile.consent_required

    return JsonResponse({"upcomingInvitations" : upcomingInvitations,
                         "pastAcceptedInvitations":pastAcceptedInvitations,
                         "consent_required":consent_required,
                         "consentFormText":p.consentForm,
                         "failed":failed}, safe=False)

#subject accepts consent form
def acceptConsentForm(data,u):
    '''
    Subject accepts consent form
    
    :param data: Form data{} empty
    :type data: dict

    :param u: Subject User
    :type u: django.contrib.auth.models.User
    '''

    logger = logging.getLogger(__name__)
    logger.info("Accept consent form")    
    logger.info(data)

    u.profile.consent_required=False
    u.profile.save()

    upcomingInvitations = u.profile.sorted_session_list_upcoming()
    consent_required = u.profile.consent_required

    return JsonResponse({"upcomingInvitations" : upcomingInvitations,
                         "consent_required":consent_required,
                         "failed":False}, safe=False)

#subject has accepted an invitation
def acceptInvitation(data,u):    
    '''
    Subject cancels invitation acceptance 
    
    :param data: Form data{"id":experiment session id}
    :type data: dict

    :param u: Subject User
    :type u: django.contrib.auth.models.User
    '''
    logger = logging.getLogger(__name__)
    logger.info(f"Accept invitation: user {u}")    
    logger.info(data)

    failed=False

    try:
        es_id = data["id"]

        qs = u.profile.sessions_upcoming(False,datetime.now(pytz.utc) - timedelta(hours=1))
        qs = qs.filter(id = es_id).first()                               #session being accepted

        if qs:
            #subject cannot attend before consent form accepted
            if u.profile.consent_required:
                logger.warning(f"Consent required before accept, user: {u}") 
                failed=True

            #check that session has not started
            if not failed:
                if qs.hoursUntilFirstStart() <= -0.25:
                    logger.warning(f"Invitation failed session started, user: {u}")            
                    failed=True

            #check session not already full
            if not failed:
                if qs.getFull(): 
                    logger.warning(f"Invitation failed accept session full, user: {u}")             
                    failed=True
            
            #check user is not already attending a recruitment violation
            if not failed:
                user_list_valid = qs.getValidUserList_forward_check([{'id':u.id}],False,0,0,[],False,1)
                logger.info(f"Accept Invitation Valid User List: {user_list_valid}")
                if not u in user_list_valid:
                    logger.warning(f"Invitation failed recruitment violation, user {u}")             
                    failed=True
            
            # #check that by attending this experiment, user will not create recruitment violation in another confirmed experiment
            # if not failed:
            #     if u.profile.check_for_future_constraints(qs):
            #         failed=True
            #         logger.info("Invitation failed future violation")

            #do a backup check that user has not already done this experiment, if prohibited
            if not failed:
                esdu = experiment_session_day_users.objects.filter(experiment_session_day__experiment_session__id = qs.id,
                                                user__id=u.id).first()
                
                if esdu.getAlreadyAttended():
                    logger.warning("Invitation failed, user has already done this experiment")
                    logger.warning(f"User: {u}, attending session: {esdu.id}")
                    failed=True
            
            #update confirmed status
            if not failed:
                logger.info(f"Accept Success: {u} {esdu}")
                experiment_session_day_users.objects.filter(experiment_session_day__experiment_session__id = qs.id,
                                                user__id=u.id)\
                                        .update(confirmed=True)
            else:
                logger.warning(f"Accept Failed {u}") 

        else:
            logger.warning(f"Invitation not found {u} {esdu}")             
            failed=True

    except Exception  as e:
        logger.warning(e)
        logger.warning(f"Accept invitation error {u}")             
       
        failed=True

    upcomingInvitations = u.profile.sorted_session_list_upcoming()
    consent_required = u.profile.consent_required

    return JsonResponse({"upcomingInvitations" : upcomingInvitations,
                         "consent_required":consent_required,
                         "failed":failed}, safe=False)

#return invitations for subject
def cancelAcceptInvitation(data,u):    
    '''
    Subject cancels invitation acceptance 
    
    :param data: Form data{"id":experiment session id}
    :type data: dict

    :param u: Subject User
    :type u: django.contrib.auth.models.User
    '''
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
        failed=True

    upcomingInvitations=u.profile.sorted_session_list_upcoming()
    consent_required = u.profile.consent_required

    return JsonResponse({"upcomingInvitations" : upcomingInvitations,
                         "consent_required":consent_required,
                         "failed":failed}, safe=False)

#return list of past declined invitations
def showAllInvitations(data,u):    
    logger = logging.getLogger(__name__)
    logger.info("Show all invitations")    
    logger.info(data)

    allInvitations = u.profile.sorted_session_day_list_full()

    return JsonResponse({"allInvitations" : allInvitations}, safe=False)