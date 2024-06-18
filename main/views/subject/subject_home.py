from datetime import datetime, timedelta

import json
import logging
import pytz

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import CharField, Q, F, Value as V
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder

from main.models import ExperimentSessionDayUsers
from main.models import Parameters
from main.models import HelpDocs

from main.decorators import user_is_subject
from main.decorators import email_confirmed

from django.views import View
from django.utils.decorators import method_decorator

class SubjectHome(View):
    '''
    Subject home view
    '''

    template_name = "subject/home.html"

    @method_decorator(login_required)
    @method_decorator(user_is_subject)
    @method_decorator(email_confirmed)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logger = logging.getLogger(__name__)

        u = request.user 

        p = Parameters.objects.first()

        labManager = p.labManager

        try:
            helpText = HelpDocs.objects.annotate(rp = V(request.path,output_field=CharField()))\
                                    .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
            helpText = "No help doc was found."
        
        return render(request,self.template_name,{"labManager":labManager,
                                                  "account_paused": json.dumps(u.profile.paused, cls=DjangoJSONEncoder),
                                                  "helpText":helpText})
    
    @method_decorator(login_required)
    @method_decorator(user_is_subject)
    @method_decorator(email_confirmed)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__) 

        u = request.user

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

#return invitations for subject
def getCurrentInvitations(data,u):    
    logger = logging.getLogger(__name__)
    logger.info("Get current invitations")    
    logger.info(data)

    p = Parameters.objects.first()

    failed=False

    upcoming_invitations = u.profile.sorted_session_list_upcoming()
    past_accepted_invitations = u.profile.sorted_session_day_list_earningsOnly()
    umbrella_consents = u.profile.get_umbrella_consents()
    required_umbrella_consents = u.profile.get_required_umbrella_consents()

    return JsonResponse({"upcomingInvitations" : upcoming_invitations,
                         "pastAcceptedInvitations":past_accepted_invitations,
                         "umbrellaConsents":umbrella_consents,
                         "requiredUmbrellaConsents":required_umbrella_consents,
                         "failed":failed}, safe=False)

#subject has accepted an invitation
def acceptInvitation(data, u):    
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
    message=""

    try:
        es_id = data["id"]

        qs = u.profile.sessions_upcoming(False,datetime.now(pytz.utc) - timedelta(hours=1))
        qs = qs.filter(id = es_id).first()                               #session being accepted

        if qs:

            #check that session is not a survey
            if not failed:
                if qs.experiment.survey:
                    message=f"Invitation failed experiment is survey."
                    logger.warning(message)            
                    failed=True
           
            #check that session has not started
            if not failed:
                if qs.hoursUntilFirstStart() <= -0.25:
                    message=f"Invitation failed session started."
                    logger.warning(message)            
                    failed=True

            #check session not already full
            if not failed:
                if qs.getFull(): 
                    message=f"Invitation failed accept session full."
                    logger.warning(message)             
                    failed=True
            
            #check that user has consent form
            if not failed:                
                if not u.profile.check_for_consent(qs.consent_form):
                    message=f"Invitation failed no consent."
                    logger.warning(message)             
                    failed=True
            
            #check that user has all umbrella consents
            if not failed:                
                if len(u.profile.get_required_umbrella_consents()) > 0:
                    message=f"Invitation failed no policy consent."
                    logger.warning(message)             
                    failed=True
            
            #check user is does not have a recruitment violation
            if not failed:
                user_list_valid = qs.getValidUserList_forward_check([{'id':u.id}],False,0,0,[],False,1)
                logger.info(f"Accept Invitation Valid User List: {user_list_valid}")
                if not u in user_list_valid:
                    message = f"Invitation failed recruitment violation."
                    logger.warning(message)             
                    failed=True

            #do a backup check that user has not already done this experiment, if prohibited
            if not failed:
                esdu = ExperimentSessionDayUsers.objects.filter(experiment_session_day__experiment_session__id = qs.id,
                                                user__id=u.id).first()
                
                if esdu.getAlreadyAttended():
                    message = "Invitation failed, user has already done this experiment."
                    logger.warning(message)
                    logger.warning(f"User: {u}, attending session: {esdu.id}")
                    failed=True
                    
            
            #update confirmed status
            if not failed:
                logger.info(f"Accept Success: {u} {esdu}")
                ExperimentSessionDayUsers.objects.filter(experiment_session_day__experiment_session__id = qs.id,
                                                user__id=u.id)\
                                        .update(confirmed=True)
            else:
                logger.warning(f"Accept Failed {u}") 

        else:
            message="Invitation not found"
            logger.warning(f"Invitation not found {u} {esdu}")             
            failed=True

    except Exception as e:
        logger.warning(e)
        logger.warning(f"Accept invitation error {u}")             
       
        failed=True

    upcomingInvitations = u.profile.sorted_session_list_upcoming()

    return JsonResponse({"upcomingInvitations" : upcomingInvitations,
                         "message":message,
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
                esdu_list = ExperimentSessionDayUsers.objects\
                                       .filter(experiment_session_day__experiment_session__id = qs.id,
                                               user__id=u.id)\
                                       .filter(Q(attended=True) | Q(bumped=True))
                
                if esdu_list:
                    logger.info("Invitation failed allready attending or bumped")             
                    logger.info("User: " + str(u.id) + " Session: " + str(qs.id))
                    failed=True

                  
            if not failed:
                logger.info("Cancel Not Failed")
                ExperimentSessionDayUsers.objects.filter(experiment_session_day__experiment_session__id = qs.id,
                                                user__id=u.id)\
                                        .update(confirmed=False)
            else:
                logger.info("Cancel Accept Failed") 
        else:
            logger.info("Invitation not found")             
            logger.info("User: " + str(u.id))
            failed = True

    except Exception  as e:
        logger.warning("Cancel invitation error")             
        logger.warning("User: " + str(u.id))    
        logger.warning(e)
        failed = True

    upcomingInvitations = u.profile.sorted_session_list_upcoming()

    return JsonResponse({"upcomingInvitations":upcomingInvitations,
                         "failed":failed}, safe=False)

#return list of past declined invitations
def showAllInvitations(data, u):    
    logger = logging.getLogger(__name__)
    logger.info("Show all invitations")    
    logger.info(data)

    allInvitations = u.profile.sorted_session_day_list_full()

    return JsonResponse({"allInvitations" : allInvitations}, safe=False)