'''
Run Session View
'''
from datetime import datetime, timedelta, timezone
from decimal import *

import random
import csv
import math
import json
import logging
import pytz
import requests

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.conf import settings
from django.db.models import Q, F, CharField, Value
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist

from main.decorators import user_is_staff
from main.models import experiment_session_days, experiment_session_day_users, profile, help_docs, parameters
from main.views.staff.experimentSessionView import getManuallyAddSubject, changeConfirmationStatus

@login_required
@user_is_staff
def experimentSessionRunView(request, id_=None):
    '''
    Session Run View
    '''
    logger = logging.getLogger(__name__)

    if request.method == 'POST':

        try:
        #check for incoming file
            file_ = request.FILES['file']
            return takeEarningsUpload(file_, id_, request)
        except Exception  as exc:
            logger.info(f'experimentSessionRunView no file upload: {exc}')
            # return JsonResponse({"response" :  "error"},safe=False)

        #no incoming file
        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getSession":
            return getSession(data, id_, request.user)
        elif data["action"] == "attendSubject":
            return attendSubject(data, id_, request.user)
        elif data["action"] == "bumpSubject":
            return bumpSubject(data, id_, request.user)
        elif data["action"] == "noShowSubject":
            return noShowSubject(data, id_, request.user)
        elif data["action"] == "savePayouts":
            return savePayouts(data, id_, request.user)
        elif data["action"] == "completeSession":
            return completeSession(data, id_, request.user)
        elif data["action"] == "fillDefaultShowUpFee":
            return fillDefaultShowUpFee(data, id_, request.user)
        elif data["action"] == "backgroundSave":
            return backgroundSave(data, id_, request.user)
        elif data["action"] == "bumpAll":
            return bumpAll(data, id_, request.user)
        elif data["action"] == "autoBump":
            return autoBump(data, id_, request.user)
        elif data["action"] == "payPalExport":
            return getPayPalExport(data, id_, request.user)
        elif data["action"] == "getEarningsExport":
            return getEarningsExport(data, id_, request.user)
        elif data["action"] == "fillEarningsWithFixed":
            return fillEarningsWithFixed(data, id_, request.user)
        elif data["action"] == "stripeReaderCheckin":
            return getStripeReaderCheckin(data, id_, request.user)
        elif data["action"] == "roundEarningsUp":
            return roundEarningsUp(data, id_, request.user)
        elif data["action"] == "payPalAPI":
            return payPalAPI(data, id_, request.user)

        return JsonResponse({"response" :  "error"}, safe=False)
    
    #Get
    try:
        help_text = help_docs.objects.annotate(rp=Value(request.path, output_field=CharField()))\
                                     .filter(rp__icontains=F('path')).first().text

    except Exception  as exc:
        help_text = "No help doc was found."

    esd = experiment_session_days.objects.get(id=id_)
    return render(request, 'staff/experimentSessionRunView.html',
                  {"sessionDay":esd, "id":id_, "helpText":help_text})

#return the session info to the client
def getSession(data, id, request_user):
    logger = logging.getLogger(__name__)
    logger.info("Get Session Day")
    logger.info(data)

    esd = experiment_session_days.objects.get(id=id)

    return JsonResponse({"sessionDay" : esd.json_runInfo(request_user)}, safe=False)

#get data from the strip reader for subject checkin
def getStripeReaderCheckin(data, id, request_user):
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
    studentID = None

    try:
        if "=" in data["value"]:
            v = data["value"].split("=")
            studentID = int(v[0])
            logger.info(id)
        else:
            status = "Card Read Error"
            logger.info("Stripe Reader Error, no equals")
    except:
        status = "Card Read Error"
        logger.info("Stripe Reader card read error")

    if status == "":

        esdu = getSubjectByID(id, studentID, request_user)

        if len(esdu) > 1:
            status = "Error: Multiple users found"
            logger.info("Stripe Reader Error, multiple users found")
        else:
            if autoAddUser and request_user.is_superuser:
                status = autoAddSubject(studentID, id, request_user, ignoreConstraints)
                #status = r['status']

            if status == "":
                status = attendSubjectAction(esdu.first(), id, request_user)

    esd = experiment_session_days.objects.get(id=id)

    return JsonResponse({"sessionDay" : esd.json_runInfo(request_user), "status":status }, safe=False)

#get subjects by student id
def getSubjectByID(id, studentID, request_user):

    return  experiment_session_day_users.objects.filter(experiment_session_day__id=id,
                                                        user__profile__studentID__icontains=studentID,
                                                        confirmed=True)\
                                                .select_related('user')

#automatically add subject when during card swipe
def autoAddSubject(studentID, id, request_user, ignoreConstraints):
    logger = logging.getLogger(__name__)
    logger.info("Auto add subject")
    logger.info(studentID)

    status = ""

    p = profile.objects.filter(studentID__icontains = studentID)
    esd = experiment_session_days.objects.get(id=id)

    if len(p) > 1:
        #multiple users found
        status = "Error, Multiple users found: "

        for u in p:
            status += str(u) + " "

        logger.info(status)

    elif len(p) == 0:
        #no subject found
        status = "Error: No subject found with ID: " + str(studentID)
    else:
        #one subject found
        p = p.first()

        #check for recruitment violations
        r = json.loads(getManuallyAddSubject({"user":{"id":p.user.id},"sendInvitation":False},
                                             esd.experiment_session.id,
                                             request_user,
                                             ignoreConstraints).content.decode("UTF-8"))
        if not "success" in r['status']:
            status = f"Error: Could not add {p.user.last_name},{p.user.first_name}: Recruitment Violation"
        else:
            #confirm newly added user
            temp_esdu = esd.experiment_session_day_users_set.filter(user__id=p.user.id).first()

            if not temp_esdu:
                status = f"{p.user.last_name},{p.user.first_name} could not be added to the session, try manual add."
            else:
                r = json.loads(changeConfirmationStatus({"userId":p.user.id,
                                                         "confirmed":"confirm",
                                                         "actionAll":False,
                                                         "esduId":temp_esdu.id},
                                                        esd.experiment_session.id,
                                                        ignoreConstraints).content.decode("UTF-8"))

                if not "success" in r['status']:
                    status = f"{p.user.last_name},{p.user.first_name} added but manual confirmation is required."
    return status

#return paypal CSV
def getPayPalExport(data, id, request_user):
    '''
    export a PayPal formatted csv file for mass payment upload
    '''
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

#return earnings CSV for attending subjects
def getEarningsExport(data, id, request_user):
    '''
    list of subjects who attended and their earnings
    '''
    logger = logging.getLogger(__name__)
    logger.info("Earnings Export")
    logger.info(data)

    esd = experiment_session_days.objects.get(id=id)
    esdu = esd.experiment_session_day_users_set.filter(attended=True)

    csv_response = HttpResponse(content_type='text/csv')
    csv_response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

    writer = csv.writer(csv_response)

    s=["Last Name", "First Name", "Email", "Student ID", "Experiment Earnings", "On-Time Bonus", "Session Day ID"]
    writer.writerow(s)

    for u in esdu:
        writer.writerow(u.csv_earnings())

    return csv_response

#automatically randomly bump exccess subjects
def autoBump(data, id_, request_user):
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

    json_info = ""
    status = "success"

    try:
        esd = experiment_session_days.objects.get(id=id_)

        esdu_attended = esd.experiment_session_day_users_set.filter(attended=True)

        attendedCount = esdu_attended.count()
        bumpsNeeded = attendedCount - esd.experiment_session.recruitment_params.actual_participants

        esdu_attended_not_bumped = []

        for e in esdu_attended:
            if not e.user.profile.bumped_from_last_session(e.id):
                esdu_attended_not_bumped.append(e)

        logger.info("Auto bump: available list " + str(esdu_attended_not_bumped))

        if bumpsNeeded > len(esdu_attended_not_bumped):
            bumpsNeeded = len(esdu_attended_not_bumped)

        logger.info("Auto bump: bumps needed " + str(bumpsNeeded))

        if bumpsNeeded > 0:

            randomSample = random.sample(esdu_attended_not_bumped, bumpsNeeded)

            for u in randomSample:
                u.attended = False
                u.bumped = True
                u.save()

        json_info = esd.json_runInfo(request_user)
    except Exception  as exc:
        logger.warning(f"Auto bump error {exc}")
        status = "fail"

    return JsonResponse({"sessionDay" : json_info, "status":status}, safe=False)

#bump all subjects marked as attended
def bumpAll(data, id, request_user):
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

    json_info = ""
    status = "success"

    try:
        esd = experiment_session_days.objects.get(id=id)
        esd.experiment_session_day_users_set.filter(attended=True) \
                                            .update(attended=False,bumped=True)
        json_info = esd.json_runInfo(request_user)
    except Exception  as e:
        logger.info("Bump all error")
        logger.info(e)
        status = "fail"

    return JsonResponse({"sessionDay" : json_info, "status":status}, safe=False)

#save the payouts when user changes them
def backgroundSave(data, id, request_user):
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
def savePayouts(data, id, request_user):
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

    status = "success"

    for p in payoutList:
        #logger.info(p)
        esdu = experiment_session_day_users.objects.filter(id=p['id']).first()

        if esdu:
            try:
                esdu.earnings = max(0, Decimal(p['earnings']))
                esdu.show_up_fee = max(0, Decimal(p['showUpFee']))

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

    json_info = ""

    try:
        experiment_session_day_users.objects.bulk_update(esdu_list, ['earnings','show_up_fee'])
        esd = experiment_session_days.objects.get(id=id)
        json_info = esd.json_runInfo(request_user)
    except Exception  as exc:
        logger.warning(f"Save payouts error : {exc}")
        status = "fail"

    return JsonResponse({"sessionDay" : json_info, "status":status}, safe=False)

#close session and prevent further editing
def completeSession(data, id, request_user):
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

    status = ""
    json_info = ""

    try:
        esd = experiment_session_days.objects.get(id=id)

        status = "success"

        #check that session is not being re-opened after 24 hours by non-elevated user
        if esd.complete == True:
            if not esd.reopenAllowed(request_user):
                logger.warning(f"Failed to open session day, more 24 hours passed {esd}")
                status = "fail"

        if status == "success":
            esd.complete = not esd.complete
            esd.save()

            #clear any extra earnings fields entered
            if esd.complete:
                esdu = esd.experiment_session_day_users_set.all().filter(attended = False,bumped=False)
                esdu.update(earnings = 0, show_up_fee=0)

                esdu = esd.experiment_session_day_users_set.all().filter(bumped=True)
                esdu.update(earnings = 0)

        json_info = esd.json_runInfo(request_user)
    except Exception  as exc:
        logger.warning(f"Fill earnings with fixed amount error : {exc}")
        status = "fail"

    return JsonResponse({"sessionDay" : json_info,"status":status}, safe=False)

#fill subjects with default bump fee set in the experiments model
def fillEarningsWithFixed(data, id, request_user):
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
        json_info = esd.json_runInfo(request_user)
    except Exception  as e:
        logger.info("Fill earnings with fixed amount error : ")
        logger.info(e)
        status="fail"

    return JsonResponse({"sessionDay" : json_info,"status" : status}, safe=False)

#fill subjects with default bump fee set in the experiments model
def fillDefaultShowUpFee(data, id, request_user):
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
        json_info = esd.json_runInfo(request_user)
    except Exception  as e:
        logger.info("fill Default Show Up Fee error")
        logger.info("ID: " + str(id))
        logger.info(e)

        status="fail"

    return JsonResponse({"sessionDay" : json_info,"status" : status }, safe=False)

#mark subject as attended
def attendSubject(data, id, request_user):
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

    if request_user.is_superuser:
        status = attendSubjectAction(esdu,id,request_user)
    else:
        logger.info("Attend Subject Error, non super user")

    esd = experiment_session_days.objects.get(id=id)

    return JsonResponse({"sessionDay" : esd.json_runInfo(request_user),"status":status }, safe=False)

#mark subject as attended
def attendSubjectAction(esdu, id, request_user):
    logger = logging.getLogger(__name__)
    logger.info("Attend Subject Action")
    logger.info(esdu)

    status=""

    #check subject session day exists
    if esdu:
        #check that subject has agreed to consent form
        if esdu.user.profile.consent_required:
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
def bumpSubject(data, id, request_user):
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

    return JsonResponse({"sessionDay" : esd.json_runInfo(request_user),"status":status,"statusMessage": statusMessage}, safe=False)

#mark subject as no show
def noShowSubject(data, id, request_user):
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
        esdu.attended = False
        esdu.bumped = False
        esdu.save()
        status = "success"
    else:
        logger.info("Now Show Error, subject not found")
        status = "fail"

    esd = experiment_session_days.objects.get(id=id)

    return JsonResponse({"sessionDay" : esd.json_runInfo(request_user), "status":status}, safe=False)

#upload subject earnings from a file
def takeEarningsUpload(f, id, request):
    logger = logging.getLogger(__name__)
    logger.info("Upload earnings")

    #logger.info(f)

    esd = experiment_session_days.objects.get(id=id)
    request_user = request.user

    #format incoming data
    v = ""

    for chunk in f.chunks():
        v += str(chunk.decode("utf-8-sig"))

    logger.info(v)

    message = ""

    try:

        #parse incoming file
        v=v.splitlines()

        for i in range(len(v)):
            v[i] = v[i].split(',')

            v[i][0] = int(v[i][0])
            v[i][1] = float(v[i][1].replace('$',''))

            if len(v[i]) > 2:
                v[i][2] = float(v[i][2].replace('$',''))
            else:

                v[i].append(-1)

        logger.info(v)

        esdu_list = []

        #store earnings
        for i in v:
            esdu = getSubjectByID(id, i[0], request_user)

            # logger.info(esdu.count())

            m = ""

            if esdu.count() > 1:
                m = f'Error: More than one user found for ID {i[0]}<br>'
            elif esdu.count() == 0:
                #try to manually add user
                if request_user.is_superuser:
                    m = autoAddSubject(i[0], id, request_user, False)

                    if m != "":
                        m += "<br>"

                    esdu = getSubjectByID(id, i[0], request_user)
                else:
                    m = f'Error: No user found for ID {i[0]}<br>'

            if m.find("Error") == -1:
                if m != "":
                    message += m

                #logger.info(esdu)
                esdu = esdu.first()

                m = attendSubjectAction(esdu, id, request_user)

                if m.find("is now attending") != -1:

                    esdu.earnings = max(0, Decimal(i[1]))
                    if i[2] != -1:
                        esdu.show_up_fee = max(0, Decimal(i[2]))

                    esdu_list.append(esdu)
                else:
                    message += m + "<br>"
            else:
                message += m

        logger.info(f'Earnings import list: {esdu_list}')
        experiment_session_day_users.objects.bulk_update(esdu_list, ['earnings', 'show_up_fee', 'attended'])

    except Exception as e:
        message = f"Failed to load earnings: {e}"
        logger.info(message)

    if message == "":
        message = "Earnings Imported"

    return JsonResponse({"sessionDay" : esd.json_runInfo(request_user),
                         "message":message,
                        }, safe=False)

#round earnings up to nearest 25 cents
def roundEarningsUp(data, id, request_user):
    '''
    round earnings up to nearest 25 cents
    '''
    logger = logging.getLogger(__name__)
    logger.info("Round Earnings Up")
    logger.info(data)

    esd = experiment_session_days.objects.get(id=id)

    for i in esd.experiment_session_day_users_set.filter(attended=True):
        i.earnings = math.ceil(i.earnings*4)/4
        i.save()

    json_info = esd.json_runInfo(request_user)
    return JsonResponse({"sessionDay" : json_info}, safe=False)

#pay with PayPal API
def payPalAPI(data, id_, request_user):
    '''
    Make payment with PayPal API
    '''
    logger = logging.getLogger(__name__)
    logger.info("PayPal API")
    logger.info(data)

    parm = parameters.objects.first()

    esd = experiment_session_days.objects.get(id=id_)
    esdu_list = esd.experiment_session_day_users_set.filter(Q(show_up_fee__gt=0) | Q(earnings__gt=0))

    payments = []

    #build payments json
    for esdu in esdu_list:
        payments.append({"email": esdu.user.email, #, 'sb-8lqqw5080618@business.example.com'
                         "amount" : float(esdu.earnings + esdu.show_up_fee),
                         "note" : f'{esdu.user.first_name}, {parm.paypal_email_body}',
                         "memo" : f"SD_ID: {esdu.experiment_session_day.id}, U_ID: {esdu.user.id}"})

    data = {}
    data["info"] = {"payment_id" : id_, #, random.randrange(0, 99999999)
                    "email_subject" : parm.paypal_email_subject}

    data["items"] = payments

    logger.info(f"PayPal API Payments: {data}")

    headers = {'Content-Type' : 'application/json', 'Accept' : 'application/json'}

    req = requests.post(f'{settings.PPMS_HOST}/payments/',
                        json=data,
                        auth=(str(settings.PPMS_USER_NAME), str(settings.PPMS_PASSWORD)),
                        headers=headers)

    logger.info(f"PayPal API Payments: {req.json()}")

    error_message = ""
    result = ""

    if req.status_code == 401 or req.status_code == 403:
        error_message = "Authentication Error"
    elif req.status_code == 409:
        esd.paypal_api = True
        esd.save()
        error_message = "A mass payment has already been submitted for this session day."
    elif req.status_code != 201:
        error_message = "<div>The payments were not made because of the following errors:</div>"
        for payment in req.json():
            error_message += f'<div>{payment["data"]["email"]}: {payment["detail"]}</div>'
    else:
        esd.paypal_api = True
        esd.save()
        for payment in req.json():
            result += f'<div>{payment["email"]}: ${float(payment["amount"]):0.2f}</div>'
        #result = req.json()

    json_info = esd.json_runInfo(request_user)

    return JsonResponse({"result" : result,
                         "sessionDay" : json_info,
                         "error_message": error_message}, safe=False)
