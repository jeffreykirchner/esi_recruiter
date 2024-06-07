from datetime import timedelta
from decimal import Decimal

import json
import logging
import pytz
import re
import csv

from django.shortcuts import render
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import CharField, F, Value as V
from django.contrib.auth.models import User
from django.db.models import prefetch_related_objects
from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.views import View
from django.utils.decorators import method_decorator
from django.views.generic.detail import SingleObjectMixin
from django.http import HttpResponse

from main.decorators import user_is_staff

from main.models import ExperimentSessionDays
from main.models import ExperimentSessionDayUsers
from main.models import experiment_sessions
from main.models import parameters
from main.models import experiment_session_messages
from main.models import experiment_session_invitations
from main.models import recruitment_parameters
from main.models import help_docs
from main.models import Recruitment_parameters_trait_constraint
from main.models import Traits
from main.models import ConsentForm

from main.views.staff.user_search import lookup

from main.forms import recruitmentParametersForm
from main.forms import experimentSessionForm1
from main.forms import experimentSessionForm2
from main.forms import TraitConstraintForm

from main.globals import send_mass_email_service

import main

class ExperimentSessionView(SingleObjectMixin, View):
    '''
    experiment session view
    '''

    template_name = "staff/experiment_session.html"
    model = experiment_sessions

    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logger = logging.getLogger(__name__)

        p = parameters.objects.first()

        try:
            helpText = help_docs.objects.annotate(rp = V(request.path,output_field=CharField()))\
                                        .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
             helpText = "No help doc was found."

        es = self.get_object()

        return render(request,
                      self.template_name,
                      {'form2':experimentSessionForm2(), 
                       'form1':experimentSessionForm1(),      
                       'traitConstraintForm':TraitConstraintForm(),                                                         
                       'id': es.id,
                       'max_invitation_block_size':p.max_invitation_block_size,
                       'helpText':helpText,
                       'session':es,
                       'current_session_day_json':json.dumps(es.ESD.first().json(False), cls=DjangoJSONEncoder)
                      })
    
    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__)

        data = json.loads(request.body.decode('utf-8'))      

        id = self.get_object().id                  

        if data["status"] == "get":            
            return getSesssion(data,id)
        elif data["status"] == "updateRecruitmentParameters":
            return updateRecruitmentParameters(data,id)                     
        elif data["status"] ==  "addSessionDay":
           return addSessionDay(data,id)
        elif data["status"] ==  "removeSessionDay":
           return removeSessionDay(data,id)
        elif data["status"] ==  "updateSessionDay":
            return updateSessionDay(data,id)
        elif data["status"] ==  "removeSubject":
            return removeSubject(data,id)
        elif  data["status"] ==  "findSubjectsToInvite":
            return findSubjectsToInvite(data,id)
        elif data["status"] == "searchForSubject":
            return getSearchForSubject(data,id)
        elif data["status"] == "manuallyAddSubject":
            return getManuallyAddSubject(data,id,request.user,False)    
        elif data["status"] == "changeConfirmation":
            return changeConfirmationStatus(data,id,False)     
        elif data["status"] == "inviteSubjects":
            return inviteSubjects(data,id,request)
        elif data["status"] == "showUnconfirmedSubjects":
            return showUnconfirmedSubjects(data,id)    
        elif data["status"] == "cancelSession":
            return cancelSession(data,id)     
        elif data["status"] == "sendMessage":
            return sendMessage(data,id)
        elif data["status"] == "sendMessage":
            return sendMessage(data,id)   
        elif data["status"] == "reSendInvitation":
            return reSendInvitation(data,id) 
        elif data["status"] == "showInvitations":
            return showInvitations(data,id)  
        elif data["status"] == "showMessages":
            return showMessages(data, id)
        elif data["status"] == "updateInvitationText":
            return updateInvitationText(data,id)         
        elif data["status"] == "addTrait":
           return addTrait(data,id)
        elif data["status"] == "deleteTrait":
           return deleteTrait(data,id)
        elif data["status"] == "updateTrait":
           return updateTrait(data,id)
        elif data["status"] == "updateRequireAllTraitContraints":
           return updateRequireAllTraitContraints(data, id)
        elif data["status"] == "updateSession":
           return updateSession(data, id)
        elif data["status"] == "addToAllowList":
           return addToAllowList(data, id)
        elif data["status"] == "clearAllowList":
           return clearAllowList(data, id)
        elif data["status"] == "downloadInvitations":
            return downloadInvitations(data, id)

#get session info the show screen at load
def getSesssion(data,id):
    logger = logging.getLogger(__name__)
    logger.info("get session")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)
    
    # logger.info(es.recruitment_params)

    return JsonResponse({"session" :  es.json(),
                         "invite_to_all" : es.experiment.invite_to_all,
                         "experiment_invitation_text" : es.experiment.invitationText,
                         "recruitment_params":es.recruitment_params.json()}, safe=False)

#show all messages sent to confirmed users
def downloadInvitations(data, id):
    logger = logging.getLogger(__name__)
    logger.info("Download Invitations")
    logger.info(data)

    csv_response = HttpResponse(content_type='text/csv')
    csv_response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

    writer = csv.writer(csv_response)

    writer.writerow(['Session Day', 'Last', 'First', 'Recruiter ID', 'Public ID', 'Confirmed', 'Attended', 'Bumped'])

    es = experiment_sessions.objects.get(id=id)

    for esd in es.ESD.all().order_by('date'):
        date_string = esd.getDateStringTZOffset()
        for esdu in esd.ESDU_b.values('user__last_name', 
                                      'user__first_name', 
                                      'user__id',
                                      'user__profile__public_id',
                                      'confirmed',
                                      'attended',
                                      'bumped').all().order_by('user__last_name', 'user__first_name'):
            writer.writerow([date_string,
                             esdu['user__last_name'],
                             esdu['user__first_name'],
                             esdu['user__id'],
                             esdu['user__profile__public_id'],
                             esdu['confirmed'],
                             esdu['attended'],
                             esdu['bumped'],])

    return csv_response

#show all messages sent to confirmed users
def showInvitations(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Show Invitations")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)

    invitationList = [i.json() for i in es.experiment_session_invitations.all()]

    return JsonResponse({"invitationList" : invitationList }, safe=False)

#show all messages sent to confirmed users
def showMessages(data, id):
    logger = logging.getLogger(__name__)
    logger.info("Show Messages")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)

    messageList = [i.json() for i in es.experiment_session_messages_set.all()]

    return JsonResponse({"messageList" : messageList }, safe=False)

#send message to all confirmed subjects
def sendMessage(data, id):
    logger = logging.getLogger(__name__)
    logger.info(f"Send Message: {data}")

    params = parameters.objects.first()

    subjectText = data["subject"]
    messageText = data["text"]

    es = experiment_sessions.objects.get(id=id)

    user_list = []
    userPkList = []

    confirmed_list = es.getConfirmedEmailList()

    for i in confirmed_list:
        userPkList.append(i['user_id'])

        user_list.append({"email" : i['user_email'],
                          "variables": [{"name" : "first name", "text" : i["user_first_name"]},
                                        {"name" : "contact email", "text" : params.labManager.email}]})
            
    memo = f'Send message to session: {es.id}'

    mail_result = send_mass_email_service(user_list, subjectText, messageText, messageText, memo, len(confirmed_list) * 2)

    #logger.info(userPkList)

    #store message result
    m = experiment_session_messages()
    m.experiment_session = es
    m.subjectText = subjectText
    m.messageText = messageText
    m.mailResultSentCount = mail_result['mail_count']
    m.mailResultErrorText = mail_result['error_message']
    m.save()
    m.users.add(*userPkList)
    m.save()

    message_count = es.experiment_session_messages_set.count()

    return JsonResponse({"mailResult":mail_result, "messageCount":message_count}, safe=False)

#send invitiations again to a failed group
def reSendInvitation(data, id):
    logger = logging.getLogger(__name__)
    logger.info(f"Re-send Invitation: {data}, session {id}")

    status = "success"

    try:
        invitation = experiment_session_invitations.objects.get(id=data["id"]) 
        invitation.send_email_invitations(f"Re-send invitations for session: {id}")
    except ObjectDoesNotExist:
        status="fail"

    if status == "success":
        return JsonResponse({"status":status, "invitation" : invitation.json()}, safe=False)
    else:
        return JsonResponse({"status":status}, safe=False)
   
#cancel session
def cancelSession(data, id):
    '''
        Cancel session
        :param data: empty {}
        :type data:dict

        :param id:Experiment Session ID
        :type id:int
    '''
    logger = logging.getLogger(__name__)
    logger.info("Cancel Session")
    logger.info(data)
        
    es = experiment_sessions.objects.get(id=id)

    if es.allowEdit():       
        
        es.canceled = True

        params = parameters.objects.first()

        subjectText = params.cancelationTextSubject.replace("[session date and time]", es.getSessionDayDateString())
        messageText = es.getCancelationEmail()

        user_list = []
        userPkList = []

        confirmed_list = es.getConfirmedEmailList()

        for i in confirmed_list:
            userPkList.append(i['user_id'])

            user_list.append({"email" : i['user_email'],
                              "variables": [{"name" : "first name", "text" : i["user_first_name"]}]})
                
        memo = f'Cancel session: {es.id}'

        mail_result = send_mass_email_service(user_list, subjectText, messageText, messageText, memo, len(confirmed_list) * 2)

        logger.info(userPkList)

        es.save()
    else:
        logger.info("Cancel Session:Failed, not allowed")
        mail_result = {"mail_count":0, "error_message":"Session cannot be canceled.  Subjects have already attended."}

    return JsonResponse({"status":"success", "session" :  es.json(), "mailResult":mail_result}, safe=False)

#show unconfirmed subjects
def showUnconfirmedSubjects(data, id):
    logger = logging.getLogger(__name__)
    logger.info("Show Unconfirmed Subjects")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)

    return JsonResponse({"status":"success","es_min":es.json_esd(True)}, safe=False)

#store invitation
def storeInvitation(id, userPkList, subjectText, messageText, memo):
    logger = logging.getLogger(__name__)
    logger.info("store invitation")

    es = experiment_sessions.objects.get(id=id)

    recruitment_params = recruitment_parameters()
    recruitment_params.setup(es.recruitment_params)
    recruitment_params.save()

    m = experiment_session_invitations()
    m.experiment_session = es
    m.subjectText = subjectText
    m.messageText = messageText
    m.mailResultSentCount = 0
    m.mailResultErrorText =  "Waiting for email service."
    m.recruitment_params = recruitment_params

    m.save()
    m.users.add(*userPkList)
    m.save()

    return m.send_email_invitations(memo)

#change subject's confirmation status
def changeConfirmationStatus(data,id,ignoreConstraints,min_mode=False):
    logger = logging.getLogger(__name__)
    logger.info("Change subject's confirmation status")
    logger.info(data)

    userID = int(data["userId"])
    newStatus = data["confirmed"]
    esduId = data["esduId"]
    actionAll = data["actionAll"]

    esdu = ExperimentSessionDayUsers.objects.get(id = esduId)                                  
    
    failed = False

    if newStatus == "confirm":
        es = experiment_sessions.objects.get(id=id)

        #check user is still valid
        if not ignoreConstraints:
            u_list = es.getValidUserList_forward_check([{'id':userID}],False,0,0,[],False,1)

            if not esdu.user in u_list:
                failed=True
                logger.info("Status change fail user not in vaild list user:" + str(userID) + " session " + str(id))

        if not failed:
            esdu.confirmed = True
    else:
        if esdu.allowConfirm():
            esdu.confirmed = False
    
    esdu.save()

    #update status of all days to match
    if actionAll:
        ExperimentSessionDayUsers.objects.filter(experiment_session_day__experiment_session = esdu.experiment_session_day.experiment_session)\
                                            .filter(user = esdu.user)\
                                            .update(confirmed = esdu.confirmed)

    #if minimal mode only retur status
    if min_mode:
        return JsonResponse({"status":"success" if not failed else "fail"}, safe=False)

    es = experiment_sessions.objects.get(id=id)
    return JsonResponse({"status":"success" if not failed else "fail","es_min":es.json_esd(True)}, safe=False)

#manually search for users to add to session
def getSearchForSubject(data,id):

    logger = logging.getLogger(__name__)
    logger.info("Search for subject to maually add")
    logger.info(data)

    users_list = lookup(data["searchInfo"],False,True)

    es = experiment_sessions.objects.get(id=id)

    if len(users_list)>=1000:
        return JsonResponse({"status":"fail","message":"Error: Narrow your search"}, safe=False)

    if len(users_list)>0:
        #user_list_valid = es.getValidUserList(users_list,True,0,0,[],False) 
        user_list_valid = es.getValidUserList_forward_check(users_list,True,0,0,[],False,len(users_list))    

    for u in users_list:
        u['valid'] = 0

        #logger.info(str(u['id']))
        #logger.info(str(id))
        #check that subject is not already in
        esdu = ExperimentSessionDayUsers.objects.filter(user__id = u['id'],
                                                           experiment_session_day__experiment_session__id = id) \
                                                   .exists()

        if esdu:
            u['alreadyIn'] = 1
        else:
            u['alreadyIn'] = 0

        #check if subject violates recrutment parameters
        for uv in user_list_valid:
            if u['id'] == uv.id:
                u['valid'] = 1
                

    #logger.info(users_list)
    #logger.info(user_list_valid)

    return JsonResponse({"status":"success","users":json.dumps(list(users_list),cls=DjangoJSONEncoder)}, safe=False)

#manually add a single subject
def getManuallyAddSubject(data,id,request_user,ignoreConstraints,min_mode=False):
    '''
        Manually add a subject to a session

        :param data: Form data{"user":{"id":user id}, "sendInvitation":True/False}
        :type data: dict

        :param id: Experiment session id
        :type id: int

        :param request_user: User requesting the manual add
        :type id: django.contrib.auth.models.User

        :param ignoreConstraints: Bypass recuritment check when adding
        :type id: boolean
    '''

    logger = logging.getLogger(__name__)
    logger.info("Manually add subject")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)
    p = parameters.objects.first()
    u = data["user"]

    #check that session is not canceled
    if es.canceled:
        return JsonResponse({"status":"fail","mailResult":{"error_message":"Error: Refresh the page","mailCount":0},"user":u,"es_min":es.json_esd(False)}, safe=False)

    messageText = es.getInvitationEmail()   
    #check that message is not empty
    if not messageText or messageText == "":
        return JsonResponse({"status":"success","mailResult":{"error_message":"Error: Message is empty","mailCount":0},"user":u,"es_min":es.json_esd(False)}, safe=False)

    sendInvitation = data["sendInvitation"]

    status = "success"
    failed = False

    #check that user does not violate recruitment constraints
    if not ignoreConstraints:   
        u_list = es.getValidUserList_forward_check([{'id':u["id"]}],True,0,0,[],False,1)

        if len(u_list) == 0:
            failed=True
    elif es.checkUserInSession(User.objects.get(id = u["id"])):
         failed=True

    mail_result =  {"mail_count":0, "error_message":""}   
    
    if not failed:        
        #invite to all sessions in the future
        future_es_list=[]

        if es.experiment.invite_to_all:
            future_es_list = es.experiment.getFutureSessions()
        
        esdu_list =  es.getNewUser(u["id"], request_user, True)

        for j in future_es_list:
            esdu_list = esdu_list + j.getNewUser(u["id"], request_user, True)

        if len(esdu_list) > 0:
            main.models.ExperimentSessionDayUsers.objects.bulk_create(esdu_list, ignore_conflicts=True)

        # es.addUser(u["id"], request_user, True)
        # es.save()

        if sendInvitation:
            
            subjectText = p.invitationTextSubject.replace("[session date and time]", es.getSessionDayDateString())                            

            if len(future_es_list)>0:
                additional_dates=""

                for index, j in enumerate(future_es_list):
                    if j != es:
                        if index > 0:
                            additional_dates += "<br>"
                        additional_dates += j.getSessionDayDateString()

                messageText = messageText.replace("[additional dates]", additional_dates)

            memo = f'Manual invitation for session: {es.id}'

            mail_result = storeInvitation(id, [u["id"]], subjectText, messageText, memo) 
    else:
        status = "fail"   

    #if minimal mode only return status
    if min_mode:
         return JsonResponse({"status":status}, safe=False)

    invitationCount=es.experiment_session_invitations.count()

    return JsonResponse({"status":status,
                         "mailResult":mail_result,
                         "user":u,
                         "invitationCount":invitationCount,
                         "es_min":es.json_esd(True)}, safe=False)

#invite subjects based on recruitment parameters
def inviteSubjects(data, id, request):
    logger = logging.getLogger(__name__)
    logger.info("Invite subjects")
    logger.info(data)

    subjectInvitations = data["subjectInvitations"]

    es = experiment_sessions.objects.get(id=id)

    # logger.info(es.canceled)

    #check that session is not canceled and number of subjects is not zero
    if len(subjectInvitations) == 0 or es.canceled:
        return JsonResponse({"status":"fail", "mailResult":{"error_message":"Error: Refresh the page","mail_count":0},"userFails":0,"es_min":es.json_esd(False)}, safe=False)
    
    messageText = es.getInvitationEmail()

    #check that message is not empty
    if not messageText or messageText == "":
        return JsonResponse({"status":"fail", "mailResult":{"error_message":"Error: Message is empty","mail_count":0},"userFails":0,"es_min":es.json_esd(False)}, safe=False)

    status = "success" 
    userFails = []              #list of users failed to add
    userPkList = []             #list of primary keys of added users

    p = parameters.objects.first()

    #invite to all sessions in the future
    future_es_list=[]

    if es.experiment.invite_to_all:
        future_es_list = es.experiment.getFutureSessions()

    # #add users to session
    userPkList = []
    esdu_list = []
    for i in subjectInvitations:
        try:
            userPkList.append(i['id'])
            # es.addUser(i['id'], request.user, False)
            esdu_list = esdu_list + es.getNewUser(i['id'], request.user, False)

            for j in future_es_list:
                esdu_list = esdu_list + j.getNewUser(i['id'], request.user, False)

        except IntegrityError:
            userFails.append(i)
            status = "fail"

    if len(esdu_list) > 0:
        main.models.ExperimentSessionDayUsers.objects.bulk_create(esdu_list, ignore_conflicts=True)
            
    memo = f'Send invitations for session: {es.id}'
    subjectText = p.invitationTextSubject.replace("[session date and time]", es.getSessionDayDateString())

    if len(future_es_list)>0:
        additional_dates=""

        for index, j in enumerate(future_es_list):
            if j != es:
                if index > 0:
                    additional_dates += "<br>"
                additional_dates += j.getSessionDayDateString()

        messageText = messageText.replace("[additional dates]", additional_dates)

    mail_result = storeInvitation(id, userPkList, subjectText, messageText, memo)

    if(mail_result["error_message"] != ""):
        status = "fail"

    es.save() 

    invitationCount = es.experiment_session_invitations.count()

    return JsonResponse({"status":status,
                         "mailResult":mail_result,
                         "userFails":userFails,
                         "invitationCount":invitationCount,
                         "es_min":es.json_esd(True)}, safe=False)

#find list of subjects to invite based on recruitment parameters
def findSubjectsToInvite(data, id):
    logger = logging.getLogger(__name__)
    logger.info(f"Find subjects to invite: {data}")

    p = parameters.objects.first()

    #check valid number
    if data["number"] == "":
        number = 0
    else:
        number = int(data["number"])

    #check max block size
    if number > p.max_invitation_block_size:
        number = p.max_invitation_block_size

    es = experiment_sessions.objects.get(id=id)

    u_list_2 = es.getValidUserList_forward_check([],True,0,0,[],False,number)

    prefetch_related_objects(u_list_2,'profile')

    usersSmall2 = [u.profile.json_min() for u in u_list_2]

    return JsonResponse({"subjectInvitations" : usersSmall2,
                         "status": "success",
                         "totalValid":len(u_list_2)}, safe=False)

#update the recruitment parameters for this session
def updateRecruitmentParameters(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Update recruitment form")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)
    
    form_data_dict = {} 

    genderList=[]
    subject_typeList=[]
    institutionsExcludeList=[]
    institutionsIncludeList=[]
    experimentsExcludeList=[]
    experimentsIncludeList=[]
    schoolsExcludeList=[]
    schoolsIncludeList=[]

    for field in data["formData"]:            
        if field["name"] == "gender":                 
            genderList.append(field["value"])
        elif field["name"] == "subject_type":                 
            subject_typeList.append(field["value"])
        elif field["name"] == "institutions_exclude":                 
            institutionsExcludeList.append(field["value"])
        elif field["name"] == "institutions_include":                 
            institutionsIncludeList.append(field["value"])
        elif field["name"] == "experiments_exclude":                 
            experimentsExcludeList.append(field["value"])
        elif field["name"] == "experiments_include":                 
            experimentsIncludeList.append(field["value"])
        elif field["name"] == "schools_exclude":                 
            schoolsExcludeList.append(field["value"])
        elif field["name"] == "schools_include":                 
            schoolsIncludeList.append(field["value"])
        else:
            form_data_dict[field["name"]] = field["value"]

    form_data_dict["gender"]=genderList
    form_data_dict["subject_type"]=subject_typeList
    form_data_dict["institutions_exclude"]=institutionsExcludeList
    form_data_dict["institutions_include"]=institutionsIncludeList
    form_data_dict["experiments_exclude"]=experimentsExcludeList
    form_data_dict["experiments_include"]=experimentsIncludeList
    form_data_dict["schools_exclude"]=schoolsExcludeList
    form_data_dict["schools_include"]=schoolsIncludeList 

    #if a subject has confirmed cannot some parameters
    if es.getConfirmedCount() > 0:
        form_data_dict["allow_multiple_participations"] = "1" if es.recruitment_params.allow_multiple_participations else "0"

    #print(form_data_dict)
    form = recruitmentParametersForm(form_data_dict,instance=es.recruitment_params)

    if form.is_valid():
        #print("valid form")                
        form.save()               
        return JsonResponse({"recruitment_params":es.recruitment_params.json(),"status":"success"}, safe=False)
    else:
        logger.info("invalid recruitment form")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

#add a session day
def addSessionDay(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Add session day")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)

    if es.getConfirmedCount() == 0:

        count = int(data["count"])

        #add specified number of session days
        for i in range(count):
            esd = ExperimentSessionDays()
            
            u_list = es.ESD.first().getListOfUserIDs()

            #for i in id_list:
            #    logger.info(i)

            # logger.info(u_list)

            esd.setup(es, u_list)
            esd.save()

            es.save()

            #copy settings from most recent session day to new session and advance by one day
            lastSD = es.getLastSessionDay()

            if lastSD:
                logger.info(f"Add session day copy {lastSD}")
                esd.copy(lastSD)

                esd.date = lastSD.date + timedelta(days=1)
                esd.set_end_date()

                if lastSD.reminder_time:
                    esd.reminder_time = lastSD.reminder_time + timedelta(days=1)

                esd.save()    

    es = experiment_sessions.objects.get(id=id)
    
    return JsonResponse({"status":"success","session":es.json()}, safe=False)

#remove a session day
def removeSessionDay(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Remove session day")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)

    esd = es.ESD.get(id = data["id"])

    if esd.allowDelete():
        esd.ESDU_b.all().delete()
        esd.delete()

    es.save()

    return JsonResponse({"status":"success","sessionDays":es.json()}, safe=False)

#update session day settings
def updateSessionDay(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Update Session Day")
    logger.info(data)

    status = "success"

    es = experiment_sessions.objects.get(id=id)
    esd = ExperimentSessionDays.objects.get(id = data["id"])           

    form_data_dict = data["formData"]           

    # for field in data["formData"]:           
    #     form_data_dict[field["name"]] = field["value"]

    if es.getConfirmedCount() > 0:
        logger.warning("Cannot change session date or length when subjects have confirmed")
        form_data_dict["date"] = esd.getDateStringTZOffsetInput()
        form_data_dict["length"] = str(esd.length)
        form_data_dict["enable_time"] = 1 if esd.enable_time else 0
        #status = "fail"
    
    if form_data_dict["custom_reminder_time"] == 0:
        form_data_dict["reminder_time"] = form_data_dict["date"]

    form = experimentSessionForm2(form_data_dict,instance=esd)   

    if form.is_valid():       
        esd.save()
        esd = ExperimentSessionDays.objects.get(id = data["id"])

        #anytime experiment
        if not esd.enable_time:
            #change time to last second of the day
            p = parameters.objects.first()
            tz = pytz.timezone(p.subjectTimeZone)
            temp_d = esd.date.astimezone(tz)
            esd.date = temp_d.replace(hour=23,minute=59, second=59)
            esd.save()
            logger.info(f"updateSessionDay anytime experiment {esd.date}")
        esd.set_end_date()
                
        #if not custom reminder time, set reminder time 24 hours before start
        if not esd.custom_reminder_time:
            esd.reminder_time = esd.date - timedelta(days=1)

        esd.save()
        
        es.save()      

        print("valid session form")

        return JsonResponse({"sessionDays" :es.json(),
                             "invitationText" : es.getInvitationEmail(),
                             "status":status}, safe=False)
    else:
        print("invalid session form")
        print(dict(form.errors.items()))
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

#remove subject from session day 
def removeSubject(data,id):
    '''
        Remove subject from session

        :param data: Form data{"userId":user id, "esduId":experiment session day id}
        :type data: dict

        :param id: Experiment session id
        :type id: int

    '''
    logger = logging.getLogger(__name__)
    logger.info("Remove subject from session")
    logger.info(data)

    userId = data['userId']
    esduId = data['esduId']    

    esdu=ExperimentSessionDayUsers.objects.filter(user__id = userId,
                                                     experiment_session_day__experiment_session__id = id)

    status = "success"

    logger.info(esdu)
    #delete sessions users only if they have not earned money
    for i in esdu:
        if i.allowDelete():
            i.delete()    
        else:
            status="fail"        

    es = experiment_sessions.objects.get(id=id)
    return JsonResponse({"status":status,"es_min":es.json_esd(True)}, safe=False)
    
#update invitation text
def updateInvitationText(data,id):
    '''
        update initation text for session

        :param data: Form data{"invitationRawText":session.invitationRawText,}
        :type data: dict

        :param id: Experiment session id
        :type id: int

    '''
    logger = logging.getLogger(__name__)
    logger.info("Update Session Invitation Text")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)     

    es.invitation_text = data["invitationRawText"]
    es.save()

    return JsonResponse({"invitationText":es.getInvitationEmail(),}, safe=False) 

#add new trait constraint to parameters
def addTrait(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Add Trait Constraint")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)

    tc = Recruitment_parameters_trait_constraint()
    tc.recruitment_parameter = es.recruitment_params
    tc.trait = Traits.objects.first()
    tc.save()

    return JsonResponse({"recruitment_params":es.recruitment_params.json(),"status":"success"}, safe=False)

#delete trait constraint
def deleteTrait(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Delete Trait Constraint")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)

    t_id = data["id"]

    tc = Recruitment_parameters_trait_constraint.objects.filter(id=t_id)

    if tc:
        tc.first().delete()

    return JsonResponse({"recruitment_params":es.recruitment_params.json(),"status":"success"}, safe=False)

#update trait
def updateTrait(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Update Trait Constraint")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)

    t_id = data["trait_id"]

    tc = Recruitment_parameters_trait_constraint.objects.get(id=t_id)

    form_data_dict = data["formData"]

    # for field in data["formData"]:
    #     form_data_dict[field["name"]] = field["value"]

    form = TraitConstraintForm(form_data_dict, instance=tc)

    if form.is_valid():
                                    
        form.save()    
                                    
        return JsonResponse({"recruitment_params":es.recruitment_params.json(),"status":"success"}, safe=False)
    else:
        print("invalid form2")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

#update requireAllTraitContraints
def updateRequireAllTraitContraints(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Update Require All Trait Constraints")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)

    v = data["value"]

    if v==True:
        es.recruitment_params.trait_constraints_require_all=True
    else:
        es.recruitment_params.trait_constraints_require_all=False
    
    es.recruitment_params.save()
    
    return JsonResponse({"recruitment_params":es.recruitment_params.json(),"status":"success"}, safe=False)

#update experiment parameters
def updateSession(data, id):
    logger = logging.getLogger(__name__)
    logger.info(f"Update session: {data}")

    s = experiment_sessions.objects.get(id=id)

    form_data_dict = data["formData"]
    institutionList=[]               

    # for field in data["formData"]:            
    #     form_data_dict[field["name"]] = field["value"]

    if not s.allowEdit():
        form_data_dict["consent_form"] = s.consent_form

    form = experimentSessionForm1(form_data_dict, instance=s)

    if not s.allowEdit():
        form.fields['consent_form'].queryset = ConsentForm.objects.all()

    if form.is_valid():           
        session=form.save()               
        return JsonResponse({"session" : session.json(), "status":"success"}, safe=False)
    else:
        print("invalid experiment session form1")
        return JsonResponse({"status":"fail", "errors":dict(form.errors.items())}, safe=False)

#update subjects allowed in session
def addToAllowList(data, id):
    logger = logging.getLogger(__name__)
    logger.info(f"addToAllowList session: {data}")

    form_data_dict = data["formData"]

    message = ""

    user_id_list = User.objects.all().values_list('id', flat=True)
    not_found_list = []

    try:

        #parse incoming file
        v=form_data_dict["allowed_list"].splitlines()

        id_list = []

        for i in range(len(v)):
            v[i] = re.split(r',|\t',v[i])

            for j in v[i]:
                temp_id = int(j)
                if temp_id not in id_list:

                    #check that vaid user id
                    if temp_id not in user_id_list:
                        not_found_list.append(temp_id)
                    else:
                        id_list.append(temp_id)

    except ValueError as e:
        message = f"Failed to load earnings: Invalid ID format"
        logger.info(message)
    except Exception as e:
        message = f"Failed to load earnings: {e}"
        logger.info(message)

    logger.info(f"addToAllowList found: {id_list}")
    logger.info(f"addToAllowList not found: {not_found_list}")

    if len(not_found_list) > 0:
        return JsonResponse({"not_found_list" : not_found_list,
                             "status" : "fail"}, safe=False)
                   
    experiment_session = experiment_sessions.objects.get(id=id)

    for i in id_list:
        if not experiment_session.recruitment_params.allowed_list:
            experiment_session.recruitment_params.allowed_list = []

        if i not in experiment_session.recruitment_params.allowed_list:
            experiment_session.recruitment_params.allowed_list.append(i)
    
    experiment_session.recruitment_params.save()

    return JsonResponse({"recruitment_params" : experiment_session.recruitment_params.json(), "status" : "success"}, safe=False)

#allow all subjects into session
def clearAllowList(data, id):
    logger = logging.getLogger(__name__)
    logger.info(f"clearAllowList session: {data}")

    s = experiment_sessions.objects.get(id=id)

    form_data_dict = data["formData"]

    experiment_session = experiment_sessions.objects.get(id=id)

    experiment_session.recruitment_params.allowed_list = []
    experiment_session.recruitment_params.save()
                   
    return JsonResponse({"recruitment_params" : experiment_session.recruitment_params.json(), "status":"success"}, safe=False)