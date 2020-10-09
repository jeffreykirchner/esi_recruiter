from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
import logging
from decimal import *
from django.db.models import Q,F,CharField,Value
import random
import csv
from django.http import HttpResponse
from datetime import datetime, timedelta,timezone
from django.core.exceptions import ObjectDoesNotExist

from main.models import experiment_session_days,experiment_session_day_users,profile,help_docs
from main.views.staff.experimentSessionView import getManuallyAddSubject,changeConfirmationStatus

@login_required
@user_is_staff
def experimentSessionRunView(request,id=None):
    logger = logging.getLogger(__name__) 
        
    # logger.info("some info")

    if request.method == 'POST':       

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getSession":
            return getSession(data,id)
        elif data["action"] == "attendSubject":
            return attendSubject(request.user,data,id)
        elif data["action"] == "bumpSubject":
            return bumpSubject(data,id)
        elif data["action"] == "noShowSubject":
            return noShowSubject(data,id)
        elif data["action"] == "savePayouts":
            return savePayouts(data,id)
        elif data["action"] == "completeSession":
            return completeSession(data,id)
        elif data["action"] == "fillDefaultShowUpFee":
            return fillDefaultShowUpFee(data,id)
        elif data["action"] == "backgroundSave":
            return backgroundSave(data,id)
        elif data["action"] == "bumpAll":
            return bumpAll(data,id)
        elif data["action"] == "autoBump":
            return autoBump(data,id)
        elif data["action"] == "payPalExport":
            return getPayPalExport(data,id)
        elif data["action"] == "fillEarningsWithFixed":
            return fillEarningsWithFixed(data,id)
        elif data["action"]=="stripeReaderCheckin":
            return getStripeReaderCheckin(data,id,request.user)
           
        return JsonResponse({"response" :  "error"},safe=False)       
    else:

        try:
            helpText = help_docs.objects.annotate(rp = Value(request.path,output_field=CharField()))\
                                    .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
             helpText = "No help doc was found."

        esd = experiment_session_days.objects.get(id=id)
        return render(request,'staff/experimentSessionRunView.html',{"sessionDay":esd ,
                                                                     "id":id,
                                                                     "helpText":helpText})  

#return the session info to the client
def getSession(data,id):    
    logger = logging.getLogger(__name__)
    logger.info("Get Session Day")
    logger.info(data)

    esd = experiment_session_days.objects.get(id=id)

    return JsonResponse({"sessionDay" : esd.json_runInfo() }, safe=False)

#get data from the strip reader for subject checkin
def getStripeReaderCheckin(data,id,request_user):
    '''
    Check subject in with strip reader

    :param data: Form data{"value":stripe reader input ###=##,"autoAddUsers":True/False,"ignoreConstraints":"True/False"}
    :type data: dict

    :param id: Experiment session day id
    :type id: int
    '''
    logger = logging.getLogger(__name__)
    logger.info("Stripe Reader Checkin")
    logger.info(data)

    autoAddUser = data["autoAddUsers"]
    ignoreConstraints = data["ignoreConstraints"]

    status = ""    

    try:
        if "=" in data["value"]:
            v = data["value"].split("=")
            studentID = int(v[0])
            logger.info(id)
        else:
            status="Card Read Error"
            logger.info("Stripe Reader Error, no equals")
    except:
        status="Card Read Error"
        logger.info("Stripe Reader card read error")

    if status == "":
                    
        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = id,
                                                            user__profile__studentID__icontains = studentID,
                                                            confirmed = True)\
                                                    .select_related('user')
        
        if len(esdu)>1:
            status= "Error: Multiple users found" 
            logger.info("Stripe Reader Error, multiple users found")
        else:
            if autoAddUser and request_user.is_superuser :
                status = autoAddSubject(studentID,id,request_user,ignoreConstraints)
                #status = r['status']
            
            if status=="":
                status = attendSubjectAction(esdu.first(),id)


    esd = experiment_session_days.objects.get(id=id)

    return JsonResponse({"sessionDay" : esd.json_runInfo(),"status":status }, safe=False)

def autoAddSubject(studentID,id,request_user,ignoreConstraints):
    logger = logging.getLogger(__name__)
    logger.info("Auto add subject")
    logger.info(studentID)

    status = ""

    p = profile.objects.filter(studentID__icontains = studentID)
    esd = experiment_session_days.objects.get(id=id)

    if len(p)>1:
        #multiple users found
        status= "Error, Multiple users found: "

        for u in p:
            status += str(u) + " "

        logger.info(status)
        
    elif len(p) == 0:
        #no subject found
        status= "Error: No subject found with ID: " + str(studentID)
    else:
        #one subject found
        p = p.first()

        #check for recruitment violations
        r = json.loads(getManuallyAddSubject({"user":{"id":p.user.id},"sendInvitation":False},
                                             esd.experiment_session.id,
                                             request_user,
                                             ignoreConstraints).content.decode("UTF-8"))
        if not "success" in r['status']:
            status = "Could not add subject: Recruitment Violation"
        else:
            #confirm newly added user
            temp_esdu = esd.experiment_session_day_users_set.filter(user__id = p.user.id).first()

            if not temp_esdu:
                status = "The subject could not be added to the session, try manual add."
            else:
                r = json.loads(changeConfirmationStatus({"userId":p.user.id,
                                                        "confirmed":"confirm",
                                                        "esduId":temp_esdu.id},
                                                        esd.experiment_session.id,
                                                        ignoreConstraints).content.decode("UTF-8"))
                
                if not "success" in r['status']:
                    status = "Subject added but manual confirmation is required."
    

    return status

#return paypal CSV
def getPayPalExport(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Pay Pal Export")
    logger.info(data)

    esd = experiment_session_days.objects.get(id=id)
    esdu = esd.experiment_session_day_users_set.filter(Q(show_up_fee__gt = 0) | Q(earnings__gt = 0))

    csv_response = HttpResponse(content_type='text/csv')
    csv_response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

    writer = csv.writer(csv_response)

    for u in esdu:
        writer.writerow(u.csv_payPal())  
    
    return csv_response

#automatically randomly bump exccess subjects
def autoBump(data,id):
    '''
        mark all attended subjects as bumped

        :param data: empty {}
        :type data:dict

        :param data: Experiment Session Day ID
        :type data:int
    '''
    logger = logging.getLogger(__name__)
    logger.info("Auto Bump")
    logger.info(data)

    json_info=""
    status="success"

    try:
        esd = experiment_session_days.objects.get(id=id)

        esdu_attended = esd.experiment_session_day_users_set.filter(attended=True)

        attendedCount = esdu_attended.count()
        bumpsNeeded = attendedCount - esd.experiment_session.recruitment_params.actual_participants

        esdu_attended_not_bumped=[]

        for e in esdu_attended:
            if not e.user.profile.bumped_from_last_session(e.id):
                esdu_attended_not_bumped.append(e)

        logger.info("Auto bump: available list " + str( esdu_attended_not_bumped))

        if bumpsNeeded>len(esdu_attended_not_bumped):
                bumpsNeeded = len(esdu_attended_not_bumped)

        logger.info("Auto bump: bumps needed " + str(bumpsNeeded))

        if bumpsNeeded > 0:        

            randomSample = random.sample(esdu_attended_not_bumped, bumpsNeeded)
            
            for u in randomSample:
                u.attended = False
                u.bumped = True
                u.save() 

        json_info = esd.json_runInfo() 
    except Exception  as e:   
        logger.info("Auto bump error")
        logger.info(e)
        status = "fail"

    return JsonResponse({"sessionDay" : json_info,"status":status}, safe=False)

#bump all subjects marked as attended
def bumpAll(data,id):
    '''
        mark all attended subjects as bumped

        :param data: empty {}
        :type data:dict

        :param data: Experiment Session Day ID
        :type data:int
    '''

    logger = logging.getLogger(__name__)
    logger.info("Bump All")
    logger.info(data)

    json_info=""
    status="success"

    try:
        esd = experiment_session_days.objects.get(id=id)
        esd.experiment_session_day_users_set.filter(attended=True) \
                                            .update(attended = False,bumped = True) 
        json_info=esd.json_runInfo()
    except Exception  as e:
        logger.info("Bump all error")
        logger.info(e)
        status = "fail"

    return JsonResponse({"sessionDay" :  json_info,"status":status}, safe=False)

#save the payouts when user changes them
def backgroundSave(data,id):
    '''
        Automaically save earnings in background
        :param data: {id:id,earing:earings,showUpFee:showUpFee}
        :type data:dict

        :param data: Experiment Session Day ID
        :type data:int
    '''

    logger = logging.getLogger(__name__)
    logger.info("Background Save")
    logger.info(data)

    payoutList = data['payoutList']

    #time_start = datetime.now()

    esdu_list=[]
    status="success"

    for p in payoutList:
        #logger.info(p)
        esdu  = experiment_session_day_users.objects.filter(id = p['id']).first()

        if esdu:
            try:
                esdu.earnings = max(0,Decimal(p['earnings']))
                esdu.show_up_fee = max(0,Decimal(p['showUpFee']))
            except Exception  as e:
                logger.info("Background Save Error : ")
                logger.info(e)
                logger.info(p)
                esdu.earnings = 0
                esdu.show_up_fee = 0
                status = "fail"
            
            esdu_list.append(esdu)
        else:
            logger.info("Baground save error user not found")
            status = "fail"

    try:    
        experiment_session_day_users.objects.bulk_update(esdu_list, ['earnings','show_up_fee'])
    except Exception  as e:
        logger.info(e)
        status = "fail"
    

    #time_end = datetime.now()
    #time_span = time_end-time_start

    #logger.info("SQL Run time: " + str(time_span.total_seconds()))

    return JsonResponse({"status" :status }, safe=False)

#save the currently entered payouts
def savePayouts(data,id):
    '''
        Complete session after all earnings have been entered
        :param data: empty {id:id,earing:earings,showUpFee:showUpFee}
        :type data:dict

        :param data: Experiment Session Day ID
        :type data:int
    '''
    logger = logging.getLogger(__name__)
    logger.info("Save Payouts")
    logger.info(data)

    payoutList = data['payoutList']

    esdu_list = []

    status="success"

    for p in payoutList:
        #logger.info(p)
        esdu  = experiment_session_day_users.objects.filter(id = p['id']).first()

        if esdu:
            try:
                esdu.earnings = max(0,Decimal(p['earnings']))
                esdu.show_up_fee = max(0,Decimal(p['showUpFee']))

            except Exception  as e:
                logger.info("Save Error : ")
                logger.info(p)
                logger.info(e)
                esdu.earnings = 0
                esdu.show_up_fee = 0
                status = "fail"
            
            esdu_list.append(esdu)
        else:
            logger.info("Save payouts error user not found")
            status = "fail"
        
    json_info=""

    try:
        experiment_session_day_users.objects.bulk_update(esdu_list, ['earnings','show_up_fee'])
        esd = experiment_session_days.objects.get(id=id)
        json_info = esd.json_runInfo()
    except Exception  as e:
        logger.info("Save payouts error : ")
        logger.info(e)
        status="fail"

    return JsonResponse({"sessionDay" : json_info,"status":status}, safe=False)

#close session and prevent further editing
def completeSession(data,id):
    '''
        Complete session after all earnings have been entered
        :param data: empty {}
        :type data:dict

        :param data: Experiment Session Day ID
        :type data:int

    '''
    logger = logging.getLogger(__name__)
    logger.info("Complete Session")
    logger.info(data)

    status=""
    json_info=""

    try:
        esd = experiment_session_days.objects.get(id=id)

        esd.complete = not esd.complete
        esd.save()

        #clear any extra earnings fields entered
        if esd.complete:
            esdu = esd.experiment_session_day_users_set.all().filter(attended = False,bumped=False)
            esdu.update(earnings = 0, show_up_fee=0)

            esdu = esd.experiment_session_day_users_set.all().filter(bumped=True)
            esdu.update(earnings = 0)
        
        status="success"
        json_info = esd.json_runInfo()
    except Exception  as e:
        logger.info("Fill earnings with fixed amount error : ")
        logger.info(e)
        status="fail"

    return JsonResponse({"sessionDay" : json_info,"status":status}, safe=False)

#fill subjects with default bump fee set in the experiments model
def fillEarningsWithFixed(data,id):
    '''
    Set all attended subjects earnings to specified amount

    :param data: Form data{"amount":earnings}
    :type data: dict

    :param id: Experiment session day id
    :type id: int
    '''
    logger = logging.getLogger(__name__)
    logger.info("Fill Earnings with fixed amount")
    logger.info(data)

    status=""
    json_info=""

    try:
        esd = experiment_session_days.objects.get(id=id)

        amount = data["amount"]

        esd.experiment_session_day_users_set.filter(attended=True) \
                                            .update(earnings = Decimal(amount))
        
        status="success"
        json_info = esd.json_runInfo()
    except Exception  as e:
        logger.info("Fill earnings with fixed amount error : ")
        logger.info(e)
        status="fail"

    return JsonResponse({"sessionDay" : json_info,"status" : status}, safe=False)

#fill subjects with default bump fee set in the experiments model
def fillDefaultShowUpFee(data,id):
    '''
    Set attended subjects bump fee to default

    :param data: Form data{} empty
    :type data: dict

    :param id: Experiment session day id
    :type id: int
    '''
    logger = logging.getLogger(__name__)
    logger.info("Fill Default Show Up Fee")
    logger.info(data)

    status=""
    json_info=""

    try:
        esd = experiment_session_days.objects.get(id=id)

        showUpFee = esd.experiment_session.experiment.showUpFee
        #logger.info(showUpFee)

        esd.experiment_session_day_users_set.filter(Q(attended=True)|Q(bumped=True)) \
                                            .update(show_up_fee = showUpFee)

        #logger.info(esd.experiment_session_day_users_set.filter(Q(attended=True)|Q(bumped=True)))
        
        status="success"
        json_info = esd.json_runInfo()
    except Exception  as e:
        logger.info("fill Default Show Up Fee error")             
        logger.info("ID: " + str(id))    
        logger.info(e)

        status="fail"

    return JsonResponse({"sessionDay" : json_info,"status" : status }, safe=False)

#mark subject as attended
def attendSubject(u,data,id):
    '''
        Mark subject as attended in a session day

        :param u: request user object
        :type u:django.contrib.auth.models.User

        :param data: {id:experiment_session_day_users.id}
        :type data:dict

        :param id:experiment session day id
        :type id:main.models.experiment_session_day
    '''    
    logger = logging.getLogger(__name__)
    logger.info("Attend Subject")
    logger.info(data)
    
    esdu = experiment_session_day_users.objects.filter(id=data['id']).first()

    logger.info(data)

    status=""

    if u.is_superuser:
        status = attendSubjectAction(esdu,id)
    else:
        logger.info("Attend Subject Error, non super user")

    esd = experiment_session_days.objects.get(id=id)

    return JsonResponse({"sessionDay" : esd.json_runInfo(),"status":status }, safe=False)

#mark subject as attended
def attendSubjectAction(esdu,id):
    logger = logging.getLogger(__name__)
    logger.info("Attend Subject Action")
    logger.info(esdu)

    status=""

    #check subject session day exists
    if esdu:
        #check that subject has agreed to consent form
        if esdu.user.profile.consentRequired:
            esdu.bumped = False
            esdu.attended = False

            status = esdu.user.last_name + ", " + esdu.user.first_name + " must agree to the consent form."
            logger.info("Conset required:user" + str(esdu.user.id) + ", " + " ESDU: " + str(esdu.id))

        #check if user has confirmed for session
        elif not esdu.confirmed:
            esdu.attended = False
            esdu.bumped = False
            
            status = esdu.user.last_name + ", " + esdu.user.first_name + " has not confirmed."
            logger.info("User has not confirmed:user" + str(esdu.user.id) + ", " + " ESDU: " + str(esdu.id))

        #backup check that subject has not already done this experiment if excluded
        elif esdu.getAlreadyAttended():
            esdu.attended = False
            esdu.bumped = True
            
            status = esdu.user.last_name + ", " + esdu.user.first_name + " has already done this experiment."
            logger.info("Double experiment checkin attempt:user" + str(esdu.user.id) + ", " + " ESDU: " + str(esdu.id))
        
        #attend subject
        else:     
            esdu.attended = True
            esdu.bumped = False

            status = esdu.user.last_name + ", " + esdu.user.first_name + " is now attending."

        esdu.save()          
    else:           
        status = "No subject found."

    return status

#mark subject as bumped
def bumpSubject(data,id):   
    '''
        Mark subject as attended in a session day

        :param data: {id:experiment_session_day_users.id}
        :type data:dict

        :param id:experiment session day id
        :type id:main.models.experiment_session_day
    '''

    logger = logging.getLogger(__name__)
    logger.info("Bump Subject")
    logger.info(data)

    esdu = experiment_session_day_users.objects.filter(id=data['id']).first()

    status=""
    statusMessage=""

    if esdu:
        if esdu.confirmed:
            esdu.attended=False
            esdu.bumped=True

            statusMessage = esdu.user.last_name + ", " + esdu.user.first_name + " is now bumped."
            status="success"
        else:
            esdu.attended = False
            esdu.bumped = False           

            statusMessage = esdu.user.last_name + ", " + esdu.user.first_name + " has not confirmed."
            logger.info("User has not confirmed:user" + str(esdu.user.id) + ", " + " ESDU: " + str(esdu.id))
            status="fail"

        esdu.save()
    else:       
        statusMessage =  "Bump Error, subject not found"
        logger.info(statusMessage)
        status="fail"

    esd = experiment_session_days.objects.get(id=id)    

    return JsonResponse({"sessionDay" : esd.json_runInfo(),"status":status,"statusMessage": statusMessage}, safe=False)

#mark subject as no show
def noShowSubject(data,id):    
    '''
    Set subject to "No Show" status

    :param data: Form data{"id":experiment session day user id}
    :type data: dict

    :param id: Experiment session day id
    :type id: int
    '''
    logger = logging.getLogger(__name__)
    logger.info("No Show")
    logger.info(data)

    esdu = experiment_session_day_users.objects.filter(id=data['id']).first()

    status = ""
    
    if esdu:
        esdu.attended=False
        esdu.bumped=False
        esdu.save()
        status = "success"
    else:
        logger.info("Now Show Error, subject not found")
        status = "fail"

    esd = experiment_session_days.objects.get(id=id)

    return JsonResponse({"sessionDay" : esd.json_runInfo(),"status":status}, safe=False)