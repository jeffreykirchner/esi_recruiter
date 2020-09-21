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
                        recruitment_parameters
from main.forms import recruitmentParametersForm,experimentSessionForm2
from django.http import JsonResponse
from django.forms.models import model_to_dict
import json
from django.conf import settings
import logging
from django.db.models import CharField,Q,F,Value as V,Subquery
from django.contrib.auth.models import User
import random
import datetime
from django.db.models import prefetch_related_objects
from .userSearch import lookup
from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError
from . import sendMassEmail
from datetime import timedelta

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
            return getManuallyAddSubject(data,id,request)    
        elif data["status"] == "changeConfirmation":
            return changeConfirmationStatus(data,id)     
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

    else: #GET             

        return render(request,
                      'staff/experimentSessionView.html',
                      {'updateRecruitmentParametersForm':recruitmentParametersForm(),    
                       'form2':experimentSessionForm2(),                                                               
                       'id': id,
                       'session':experiment_sessions.objects.get(id=id)})

#get session info the show screen at load
def getSesssion(data,id):
    logger = logging.getLogger(__name__)
    logger.info("get session")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)
    
    logger.info(es.recruitment_params)

    return JsonResponse({"session" :  es.json(),
                         "recruitment_params":es.recruitment_params.json()}, safe=False)

#show all messages sent to confirmed users
def showInvitations(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Show Invitations")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)

    invitationList = [i.json() for i in es.experiment_session_invitations_set.all()]

    return JsonResponse({"invitationList" : invitationList }, safe=False)

#show all messages sent to confirmed users
def showMessages(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Show Messages")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)

    messageList = [i.json() for i in es.experiment_session_messages_set.all()]

    return JsonResponse({"messageList" : messageList }, safe=False)

#send message to all confirmed subjects
def sendMessage(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Send Message")
    logger.info(data)

    subjectText =  data["subject"]
    messageText = data["text"]

    es = experiment_sessions.objects.get(id=id)

    emailList = []
    userPkList = []
    
    for i in es.getConfirmedEmailList():
        emailList.append({"email":i['user_email'],"first_name":i["user_first_name"]})
        userPkList.append(i['user_id'])

    mailResult = sendMassEmail(emailList,subjectText, messageText)

    logger.info(userPkList)

    #store message result
    m = experiment_session_messages()
    m.experiment_session = es
    m.subjectText = subjectText
    m.messageText = messageText
    m.mailResultSentCount = mailResult['mailCount']
    m.mailResultErrorText = mailResult['errorMessage']
    m.save()
    m.users.add(*userPkList)
    m.save()

    messageCount=es.experiment_session_messages_set.count()

    return JsonResponse({"mailResult":mailResult,"messageCount":messageCount}, safe=False)

#cancel session
def cancelSession(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Cancel Session")
    logger.info(data)
        
    es = experiment_sessions.objects.get(id=id)

    if es.allowDelete():
        es.canceled = True

        esd =  es.ESD.order_by("date").first()
        logger.info(esd.date)

        p = parameters.objects.get(id=1)
        subjectText = p.cancelationTextSubject

        emailList = []
        
        for i in es.getConfirmedEmailList():
            emailList.append({"email":i['user_email'],"first_name":i["user_first_name"]})

        mailResult = sendMassEmail(emailList,subjectText, es.getCancelationEmail())

        es.save()
    else:
        logger.info("Cancel Session:Failed, not allowed")
        mailResult = {"mailCount":0,"errorMessage":"Session cannot be canceled.  Subjects have already attended."}

    return JsonResponse({"status":"success","session" :  es.json(),"mailResult":mailResult}, safe=False)

#show unconfirmed subjects
def showUnconfirmedSubjects(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Show Unconfirmed Subjects")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)

    return JsonResponse({"status":"success","es_min":es.json_esd(True)}, safe=False)

#invite subjects based on recruitment parameters
def inviteSubjects(data,id,request):
    logger = logging.getLogger(__name__)
    logger.info("Invite subjects")
    logger.info(data)

    subjectInvitations = data["subjectInvitations"]

    es = experiment_sessions.objects.get(id=id)

    logger.info(es.canceled)

    if len(subjectInvitations) == 0 or es.canceled:
        return JsonResponse({"status":"fail","mailResult":{"errorMessage":"Error: Refresh the page","mailCount":0},"userFails":0,"es_min":es.json_esd(False)}, safe=False)
    
    status = "success" 
    userFails = []              #list of users failed to add
    userSuccesses = []          #list of users add
    userPkList = []             #list of primary keys of added users

    p = parameters.objects.get(id=1)
    subjectText = ""

    if es.ESD.count() == 1:
        subjectText = p.invitationTextSubject
    else:
        subjectText = p.invitationTextMultiDaySubject

    messageText = es.getInvitationEmail()

    #add users to session
    for i in subjectInvitations:
        try:
            es.addUser(i['id'],request.user,False)
            userSuccesses.append(i)
            userPkList.append(i['id'])
        except IntegrityError:
            userFails.append(i)
            status = "fail"
    
    #send emails
    mailResult = sendMassEmail(userSuccesses, subjectText, messageText)

    if(mailResult["errorMessage"] != ""):
        status = "fail"

    es.save()

    #store invitation
    recruitment_params = recruitment_parameters()
    recruitment_params.setup(es.recruitment_params)
    recruitment_params.save()

    m = experiment_session_invitations()
    m.experiment_session = es
    m.subjectText = subjectText
    m.messageText = messageText
    m.mailResultSentCount = mailResult['mailCount']
    m.mailResultErrorText = mailResult['errorMessage']  
    m.recruitment_params = recruitment_params

    m.save()
    m.users.add(*userPkList)
    m.save()

    invitationCount=es.experiment_session_invitations_set.count()

    return JsonResponse({"status":status,
                         "mailResult":mailResult,
                         "userFails":userFails,
                         "invitationCount":invitationCount,
                         "es_min":es.json_esd(True)}, safe=False)

#change subject's confirmation status
def changeConfirmationStatus(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Change subject's confirmation status")
    logger.info(data)

    userID = int(data["userId"])
    newStatus = data["confirmed"]
    esduId = data["esduId"]

    esdu = experiment_session_day_users.objects.get(id = esduId)                                  
    
    if newStatus == "confirm":
        if not esdu.getAlreadyAttended():
            esdu.confirmed = True
    else:
        if esdu.allowConfirm():
            esdu.confirmed = False
    
    esdu.save()

    es = experiment_sessions.objects.get(id=id)
    return JsonResponse({"status":"success","es_min":es.json_esd(True)}, safe=False)

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
        user_list_valid = es.getValidUserList(users_list,True,0,0)    

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
                
                #check that this experiment does not violate another accepted experiment
                if not uv.profile.check_for_future_constraints(es):                    
                    u['valid'] = 1
                
                break

    #logger.info(users_list)
    #logger.info(user_list_valid)

    return JsonResponse({"status":"success","users":json.dumps(list(users_list),cls=DjangoJSONEncoder)}, safe=False)

#manually add a single subject
def getManuallyAddSubject(data,id,request):

    logger = logging.getLogger(__name__)
    logger.info("Manually add subject")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)

    if es.canceled:
        return JsonResponse({"status":"fail","mailResult":{"errorMessage":"Error: Refresh the page","mailCount":0},"user":"","es_min":es.json_esd(False)}, safe=False)

    u = data["user"]
    sendInvitation = data["sendInvitation"]

    status = "success"

    #check the subject not already in session
    esdu = experiment_session_day_users.objects.filter(user__id = u["id"],
                                                           experiment_session_day__experiment_session__id = id) \
                                                   .exists()    

    mailResult =  {"mailCount":0,"errorMessage":""}

    p = parameters.objects.get(id=1)
    subjectText = ""

    if es.ESD.count() == 1:
        subjectText = p.invitationTextSubject
    else:
        subjectText = p.invitationTextMultiDaySubject

    if not esdu:
       es.addUser(u["id"],request.user,True)
       es.save()
       if sendInvitation:
           mailResult = sendMassEmail([u], subjectText, es.getInvitationEmail())
       else:
           mailResult =  {"mailCount":0,"errorMessage":""}    
    else:
        status = "fail"    

    return JsonResponse({"status":status,"mailResult":mailResult,"user":u,"es_min":es.json_esd(True)}, safe=False)
    
#find list of subjects to invite based on recruitment parameters
def findSubjectsToInvite(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Find subjects to invite")
    logger.info(data)

    number = int(data["number"])

    es = experiment_sessions.objects.get(id=id)

    u_list = es.getValidUserList([],True,0,0)

    #u_list = es.getValidUserListDjango([],True,0)

    #check that invitation does not violate previously accepted invitations
    u_list_2=[]
    for u in u_list:
        if not u.profile.check_for_future_constraints(es):
            u_list_2.append(u)

    totalValid = len(u_list_2)

    logger.info("Randomly Select:" + str(number)+ " of " + str(totalValid))

    if number > len(u_list_2):
        usersSmall = u_list_2
    else:  
        usersSmall = random.sample(u_list_2,number)

    prefetch_related_objects(usersSmall,'profile')

    usersSmall2 = [u.profile.json_min() for u in usersSmall]

    return JsonResponse({"subjectInvitations" : usersSmall2,
                         "status":"success",
                         "totalValid":str(totalValid)}, safe=False)

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
        esd = experiment_session_days()
        

        u_list = es.ESD.first().getListOfUserIDs()

        #for i in id_list:
        #    logger.info(i)

        # logger.info(u_list)

        esd.setup(es,u_list)
        esd.save()

        es.save()    

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

    es = experiment_sessions.objects.get(id=id)
    esd = experiment_session_days.objects.get(id = data["id"])           

    form_data_dict = {}            

    for field in data["formData"]:           
        form_data_dict[field["name"]] = field["value"]

    if es.getConfirmedCount() > 0:
        form_data_dict["date"] = esd.getDateStringTZOffset()
        form_data_dict["length"] = str(esd.length)

    form = experimentSessionForm2(form_data_dict,instance=esd)   

    if form.is_valid():
        esd.save()
        esd.date_end = esd.date + timedelta(minutes = esd.length)
        esd.save()
        
        es.save()      

        # es = experiment_sessions.objects.get(id=id)

        return JsonResponse({"sessionDays" :es.json(),"status":"success"}, safe=False)
    else:
        print("invalid form2")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

#remove subject from session day 
def removeSubject(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Remove subject from session")
    logger.info(data)

    userId = data['userId']
    esduId = data['esduId']    

    esdu=experiment_session_day_users.objects.filter(user__id = userId,
                                                     experiment_session_day__experiment_session__id = id)

    logger.info(esdu)
    #delete sessions users only if they have not earned money
    for i in esdu:
        if i.allowDelete():
            i.delete()            

    es = experiment_sessions.objects.get(id=id)
    return JsonResponse({"status":"success","es_min":es.json_esd(True)}, safe=False)
    

    