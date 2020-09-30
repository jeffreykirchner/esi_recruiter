from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
import logging
from decimal import *
from django.db.models import Q,F
import random
import csv
from django.http import HttpResponse
from datetime import datetime, timedelta,timezone
from django.core.exceptions import ObjectDoesNotExist

from main.models import experiment_session_days,experiment_session_day_users,profile

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
            return getStripeReaderCheckin(data,id)
           
        return JsonResponse({"response" :  "error"},safe=False)       
    else:      
        esd = experiment_session_days.objects.get(id=id)
        return render(request,'staff/experimentSessionRunView.html',{"sessionDay":esd ,"id":id})  

#return the session info to the client
def getSession(data,id):    
    logger = logging.getLogger(__name__)
    logger.info("Get Session Day")
    logger.info(data)

    esd = experiment_session_days.objects.get(id=id)

    return JsonResponse({"sessionDay" : esd.json_runInfo() }, safe=False)

#get data from the strip reader for subject checkin
def getStripeReaderCheckin(data,id):
    '''
    Check subject in with strip reader

    :param data: Form data{"value":stripe reader input, ###=##}
    :type data: dict

    :param id: Experiment session day id
    :type id: int
    '''
    logger = logging.getLogger(__name__)
    logger.info("Stripe Reader Checkin")
    logger.info(data)

    status = ""    

    try:
        if "=" in data["value"]:
            v = data["value"].split("=")
            chapmanID = int(v[0])
            logger.info(id)
        else:
            status="Card Read Error"
            logger.info("Stripe Reader Error, no equals")
    except:
        status="Card Read Error"
        logger.info("Stripe Reader card read error")

    if status == "":
        # try:            
        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = id,
                                                            user__profile__chapmanID__icontains = chapmanID,
                                                            confirmed = True)\
                                                    .select_related('user')
        
        if len(esdu)>1:
            status= "Error: Multiple users found" 
            logger.info("Stripe Reader Error, multiple users found")
        else:
            status = attendSubjectAction(esdu.first(),id)

    esd = experiment_session_days.objects.get(id=id)

    return JsonResponse({"sessionDay" : esd.json_runInfo(),"status":status }, safe=False)

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
    logger = logging.getLogger(__name__)
    logger.info("Auto Bump")
    logger.info(data)

    esd = experiment_session_days.objects.get(id=id)

    esdu_attended = esd.experiment_session_day_users_set.filter(attended=True)

    attendedCount = esdu_attended.count()
    bumpsNeeded = attendedCount - esd.experiment_session.recruitment_params.actual_participants

    esdu_attended_not_bumped=[]

    for e in esdu_attended:
        if not e.user.profile.bumped_from_last_session(e.id):
            esdu_attended_not_bumped.append(e)

    #logger.info(esdu_attended_not_bumped)

    if bumpsNeeded>len(esdu_attended_not_bumped):
            bumpsNeeded = len(esdu_attended_not_bumped)

    if bumpsNeeded > 0:        

        randomSample = random.sample(esdu_attended_not_bumped, bumpsNeeded)
        
        for u in randomSample:
            u.attended = False
            u.bumped = True
            u.save()    
    
    return JsonResponse({"sessionDay" : esd.json_runInfo() }, safe=False)

#bump all subjects marked as attended
def bumpAll(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Bump All")
    logger.info(data)

    esd = experiment_session_days.objects.get(id=id)
    esd.experiment_session_day_users_set.filter(attended=True) \
                                        .update(attended = False,bumped = True) 

    return JsonResponse({"sessionDay" : esd.json_runInfo() }, safe=False)

#save the payouts when user changes them
def backgroundSave(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Background Save")
    logger.info(data)

    payoutList = data['payoutList']

    #time_start = datetime.now()

    esdu_list=[]

    for p in payoutList:
        #logger.info(p)
        esdu  = experiment_session_day_users.objects.get(id = p['id'])

        try:
            esdu.earnings = max(0,Decimal(p['earnings']))
            esdu.show_up_fee = max(0,Decimal(p['showUpFee']))
        except (ValueError, DecimalException):
            logger.info("Background Save Error : ")
            logger.info(p)
            esdu.earnings = 0
            esdu.show_up_fee = 0
        
        esdu_list.append(esdu)

    experiment_session_day_users.objects.bulk_update(esdu_list, ['earnings','show_up_fee'])

    status="success"

    #time_end = datetime.now()
    #time_span = time_end-time_start

    #logger.info("SQL Run time: " + str(time_span.total_seconds()))

    return JsonResponse({"status" :status }, safe=False)

#save the currently entered payouts
def savePayouts(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Save Payouts")
    logger.info(data)

    payoutList = data['payoutList']

    esdu_list = []

    for p in payoutList:
        #logger.info(p)
        esdu  = experiment_session_day_users.objects.get(id = p['id'])

        try:
            esdu.earnings = max(0,Decimal(p['earnings']))
            esdu.show_up_fee = max(0,Decimal(p['showUpFee']))

        except (ValueError, DecimalException):
            logger.info("Background Save Error : ")
            logger.info(p)
            esdu.earnings = 0
            esdu.show_up_fee = 0
        
        esdu_list.append(esdu)
    
    experiment_session_day_users.objects.bulk_update(esdu_list, ['earnings','show_up_fee'])

    esd = experiment_session_days.objects.get(id=id)

    return JsonResponse({"sessionDay" : esd.json_runInfo() }, safe=False)

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

    esd = experiment_session_days.objects.get(id=id)

    esd.complete = not esd.complete
    esd.save()

    #clear any extra earnings fields entered
    if esd.complete:
        esdu = esd.experiment_session_day_users_set.all().filter(attended = False,bumped=False)
        esdu.update(earnings = 0, show_up_fee=0)

        esdu = esd.experiment_session_day_users_set.all().filter(bumped=True)
        esdu.update(earnings = 0)

    return JsonResponse({"sessionDay" : esd.json_runInfo() }, safe=False)

#fill subjects with default bump fee set in the experiments model
def fillEarningsWithFixed(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Fill Earnings with fixed amount")
    logger.info(data)

    esd = experiment_session_days.objects.get(id=id)

    amount = data["amount"]

    try:
        esd.experiment_session_day_users_set.filter(attended=True) \
                                        .update(earnings = Decimal(amount))

    except (ValueError, DecimalException):
        logger.info("Fill earnings with fixed amount error : ")

    return JsonResponse({"sessionDay" : esd.json_runInfo() }, safe=False)

#fill subjects with default bump fee set in the experiments model
def fillDefaultShowUpFee(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Fill Default Show Up Fee")
    logger.info(data)

    esd = experiment_session_days.objects.get(id=id)

    showUpFee = esd.experiment_session.experiment.showUpFee

    esd.experiment_session_day_users_set.filter(Q(attended=True)|Q(bumped=True)) \
                                        .update(show_up_fee = showUpFee)


    return JsonResponse({"sessionDay" : esd.json_runInfo() }, safe=False)

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
    
    esdu = experiment_session_day_users.objects.get(id=data['id'])

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

        #backup check that subject has not already done this experiment if excluded
        elif not esdu.confirmed:
            esdu.attended = False
            esdu.bumped = False
            
            status = esdu.user.last_name + ", " + esdu.user.first_name + " has not confirmed."
            logger.info("User has not confirmed:user" + str(esdu.user.id) + ", " + " ESDU: " + str(esdu.id))

        elif esdu.getAlreadyAttended():
            esdu.attended = False
            esdu.bumped = True
            
            status = esdu.user.last_name + ", " + esdu.user.first_name + " has already done this experiment."
            logger.info("Double experiment checkin attempt:user" + str(esdu.user.id) + ", " + " ESDU: " + str(esdu.id))
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
    logger = logging.getLogger(__name__)
    logger.info("Bump Subject")
    logger.info(data)

    esdu = experiment_session_day_users.objects.get(id=data['id'])

    status=""
    if esdu:
        if esdu.confirmed:
            esdu.attended=False
            esdu.bumped=True

            status = esdu.user.last_name + ", " + esdu.user.first_name + " is now bumped."
        else:
            esdu.attended = False
            esdu.bumped = False           

            status = esdu.user.last_name + ", " + esdu.user.first_name + " has not confirmed."
            logger.info("User has not confirmed:user" + str(esdu.user.id) + ", " + " ESDU: " + str(esdu.id))

        esdu.save()
    else:
        status = esdu.user.last_name + ", " + esdu.user.first_name + " was not found."
        logger.info("Bump Error, subject not found")

    esd = experiment_session_days.objects.get(id=id)    

    return JsonResponse({"sessionDay" : esd.json_runInfo(),"status":status }, safe=False)

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

    esdu = experiment_session_day_users.objects.get(id=data['id'])

    status = "success"
    
    if esdu:
        esdu.attended=False
        esdu.bumped=False
        esdu.save()
    else:
        status = "fail"

    esd = experiment_session_days.objects.get(id=id)

    return JsonResponse({"sessionDay" : esd.json_runInfo(),"status":status}, safe=False)