from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from main.decorators import user_is_staff
from main.models import experiment_session_days, \
                        experiment_session_day_users, \
                        experiment_sessions, \
                        institutions, \
                        experiments, \
                        parameters,\
                        experiment_session_messages,\
                        experiment_session_invitations,\
                        recruitment_parameters,\
                        help_docs,\
                        Recruitment_parameters_trait_constraint,\
                        Traits
from main.forms import recruitmentParametersForm, experimentSessionForm2, TraitConstraintForm
from django.http import JsonResponse
from django.forms.models import model_to_dict
import json
from django.conf import settings
import logging
from django.db.models import CharField, Q, F, Value as V, Subquery
from django.contrib.auth.models import User
import random
import datetime
from django.db.models import prefetch_related_objects
from .userSearch import lookup
from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError
from main.globals import send_mass_email_service
from datetime import timedelta
import pytz

#induvidual experiment view
@login_required
@user_is_staff
def experimentSessionView(request,id):
       
    status = ""      

    if request.method == 'POST':
        
        data = json.loads(request.body.decode('utf-8'))         

        try:
            es = experiment_sessions.objects.get(id=id)  
        except es.DoesNotExist:
            raise Http404('Experiment Not Found')               

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
        elif data["status"] == "showMessages":
            return showMessages(data,id) 
        elif data["status"] == "showInvitations":
            return showInvitations(data,id)  
        elif data["status"] == "updateInvitationText":
            return updateInvitationText(data,id)         
        elif data["status"] == "addTrait":
           return addTrait(data,id)
        elif data["status"] == "deleteTrait":
           return deleteTrait(data,id)
        elif data["status"] == "updateTrait":
           return updateTrait(data,id)
        elif data["status"] == "updateRequireAllTraitContraints":
           return updateRequireAllTraitContraints(data,id)

    else: #GET             

        p = parameters.objects.first()

        try:
            helpText = help_docs.objects.annotate(rp = V(request.path,output_field=CharField()))\
                                    .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
             helpText = "No help doc was found."

        return render(request,
                      'staff/experimentSession.html',
                      {'form2':experimentSessionForm2(),      
                       'traitConstraintForm':TraitConstraintForm(),                                                         
                       'id': id,
                       'max_invitation_block_size':p.max_invitation_block_size,
                       'helpText':helpText,
                       'session':experiment_sessions.objects.get(id=id)})

#get session info the show screen at load
def getSesssion(data,id):
    logger = logging.getLogger(__name__)
    logger.info("get session")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)
    
    # logger.info(es.recruitment_params)

    return JsonResponse({"session" :  es.json(),
                         "experiment_invitation_text" : es.experiment.invitationText,
                         "recruitment_params":es.recruitment_params.json()}, safe=False)

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

    for i in es.getConfirmedEmailList():
        userPkList.append(i['user_id'])

        user_list.append({"email" : i['user_email'],
                          "variables": [{"name" : "first name", "text" : i["user_first_name"]},
                                        {"name" : "contact email", "text" : params.labManager.email}]})
            
    memo = f'Send message to session: {es.id}'

    mail_result = send_mass_email_service(user_list, subjectText, messageText, messageText, memo)

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

        subjectText = params.cancelationTextSubject
        messageText = es.getCancelationEmail()

        user_list = []
        userPkList = []

        for i in es.getConfirmedEmailList():
            userPkList.append(i['user_id'])

            user_list.append({"email" : i['user_email'],
                              "variables": [{"name" : "first name", "text" : i["user_first_name"]}]})
                
        memo = f'Cancel session: {es.id}'

        mail_result = send_mass_email_service(user_list, subjectText, messageText, messageText, memo)

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

#invite subjects based on recruitment parameters
def inviteSubjects(data, id, request):
    logger = logging.getLogger(__name__)
    logger.info("Invite subjects")
    logger.info(data)

    subjectInvitations = data["subjectInvitations"]

    es = experiment_sessions.objects.get(id=id)

    logger.info(es.canceled)

    if len(subjectInvitations) == 0 or es.canceled:
        return JsonResponse({"status":"fail", "mailResult":{"error_message":"Error: Refresh the page","mail_count":0},"userFails":0,"es_min":es.json_esd(False)}, safe=False)
    
    status = "success" 
    userFails = []              #list of users failed to add
    userSuccesses = []          #list of users add
    userPkList = []             #list of primary keys of added users

    p = parameters.objects.first()
    subjectText = ""

    subjectText = p.invitationTextSubject
    messageText = es.getInvitationEmail()

    # #add users to session
    user_list = []
    userPkList = []

    for i in subjectInvitations:
        try:
            userPkList.append(i['id'])
            es.addUser(i['id'], request.user, False)
            user_list.append({"email" : i['email'],
                              "variables": [{"name" : "first name", "text" : i["first_name"]},
                                            {"name" : "last name", "text" : i["last_name"]},
                                            {"name" : "email", "text" : i["email"]},
                                            {"name" : "recruiter id", "text" : str(i["id"])},
                                            {"name" : "student id", "text" : i["studentID"]},
                                           ]
                            })

        except IntegrityError:
            userFails.append(i)
            status = "fail"
            
    memo = f'Send invitations for session: {es.id}'

    mail_result = send_mass_email_service(user_list, subjectText, messageText, messageText, memo)

    if(mail_result["error_message"] != ""):
        status = "fail"

    es.save()

    #store invitation
    storeInvitation(id, userPkList, subjectText, messageText, mail_result['mail_count'], mail_result['error_message'])    

    invitationCount = es.experiment_session_invitations.count()

    return JsonResponse({"status":status,
                         "mailResult":mail_result,
                         "userFails":userFails,
                         "invitationCount":invitationCount,
                         "es_min":es.json_esd(True)}, safe=False)

#store invitation
def storeInvitation(id, userPkList, subjectText, messageText, mailCount, errorMessage):
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
    m.mailResultSentCount = mailCount
    m.mailResultErrorText =  errorMessage
    m.recruitment_params = recruitment_params

    m.save()
    m.users.add(*userPkList)
    m.save()

#change subject's confirmation status
def changeConfirmationStatus(data,id,ignoreConstraints):
    logger = logging.getLogger(__name__)
    logger.info("Change subject's confirmation status")
    logger.info(data)

    userID = int(data["userId"])
    newStatus = data["confirmed"]
    esduId = data["esduId"]
    actionAll = data["actionAll"]

    esdu = experiment_session_day_users.objects.get(id = esduId)                                  
    
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
        experiment_session_day_users.objects.filter(experiment_session_day__experiment_session = esdu.experiment_session_day.experiment_session)\
                                            .filter(user = esdu.user)\
                                            .update(confirmed = esdu.confirmed)

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
        esdu = experiment_session_day_users.objects.filter(user__id = u['id'],
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
def getManuallyAddSubject(data,id,request_user,ignoreConstraints):
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

    if es.canceled:
        return JsonResponse({"status":"fail","mailResult":{"errorMessage":"Error: Refresh the page","mailCount":0},"user":"","es_min":es.json_esd(False)}, safe=False)

    u = data["user"]
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
        subjectText=""
        messageText=""
       
        es.addUser(u["id"],request_user,True)
        es.save()

        if sendInvitation:
            
            user_list = []
            subjectText = p.invitationTextSubject            
            messageText = es.getInvitationEmail()

            user_list.append({"email" : u['email'],
                              "variables": [{"name" : "first name", "text" : u["first_name"]},
                                            {"name" : "last name", "text" : u["last_name"]},
                                            {"name" : "email", "text" : u["email"]},
                                            {"name" : "recruiter id", "text" : str(u["id"])},
                                            {"name" : "student id", "text" : u["profile__studentID"]},
                                           ]
                            })
            
            memo = f'Manual invitation for session: {es.id}'

            mail_result = send_mass_email_service(user_list, subjectText, messageText, messageText, memo)

        else:
            mail_result =  {"mail_count" : 0, "error_message" : ""}    

        #store invitation
        storeInvitation(id,[u["id"]], subjectText, messageText, mail_result['mail_count'], mail_result['error_message']) 
    else:
        status = "fail"   

    invitationCount=es.experiment_session_invitations.count()

    return JsonResponse({"status":status,
                         "mailResult":mail_result,
                         "user":u,
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
            esd = experiment_session_days()
            
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
        esd.experiment_session_day_users_set.all().delete()
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
    esd = experiment_session_days.objects.get(id = data["id"])           

    form_data_dict = {}            

    for field in data["formData"]:           
        form_data_dict[field["name"]] = field["value"]

    if es.getConfirmedCount() > 0:
        logger.warning("Cannot change session date or length when subjects have confirmed")
        form_data_dict["date"] = esd.getDateStringTZOffset()
        form_data_dict["length"] = str(esd.length)
        form_data_dict["enable_time"] = 'true' if esd.enable_time else 'false'
        #status = "fail"
    
    if form_data_dict["custom_reminder_time"] == 'false':
        form_data_dict["reminder_time"] = form_data_dict["date"]

    form = experimentSessionForm2(form_data_dict,instance=esd)   

    if form.is_valid():       
        esd.save()
        esd = experiment_session_days.objects.get(id = data["id"])

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

        return JsonResponse({"sessionDays" :es.json(),"status":status}, safe=False)
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

    esdu=experiment_session_day_users.objects.filter(user__id = userId,
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

    form_data_dict = {} 

    for field in data["formData"]:
        form_data_dict[field["name"]] = field["value"]

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