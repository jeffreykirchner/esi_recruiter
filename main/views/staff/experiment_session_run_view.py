'''
Run Session View
'''
from decimal import *

import random
import csv
import math
from decimal import Decimal
import json
import logging
import requests
import re

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.db.models import Q, F, CharField, Value
from django.http import HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.views import View
from django.utils.decorators import method_decorator
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.models import User

from main.decorators import user_is_staff
from main.models import experiment_session_days
from main.models import experiment_session_day_users
from main.models import profile
from main.models import help_docs
from main.models import parameters

from main.views.staff.experiment_session_view import getManuallyAddSubject, changeConfirmationStatus

class ExperimentSessionRunView(SingleObjectMixin, View):
    '''
    Experiment Session Run View
    '''

    template_name = "staff/experiment_session_run.html"
    model = experiment_session_days

    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logger = logging.getLogger(__name__)

        esd = self.get_object()
        id_ = esd.id

        try:
            help_text = help_docs.objects.annotate(rp=Value(request.path, output_field=CharField()))\
                                        .filter(rp__icontains=F('path')).first().text

        except Exception  as exc:
            help_text = "No help doc was found."

        esd = experiment_session_days.objects.get(id=id_)
        return render(request,
                      self.template_name,
                      {"sessionDay":esd, 
                       "sessionDay_json":json.dumps(esd.json_runInfo(request.user), cls=DjangoJSONEncoder),
                       "id":id_, 
                       "helpText":help_text})
    
    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__) 

        id_ = self.get_object().id

        # try:
        #     #check for incoming file
        #     file_ = request.FILES['file']
        #     return takeEarningsUpload(file_, id_, request.user, request.POST['auto_add'])
        # except Exception  as exc:
        #     logger.info(f'experimentSessionRunView no file upload: {exc}')
        #     # return JsonResponse({"response" :  "error"},safe=False)

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
        elif data["action"] == "uploadEarningsText":
            return takeEarningsUpload2(data, id_, request.user)

        return JsonResponse({"response" :  "error"}, safe=False)

#return the session info to the client
def getSession(data, id, request_user):
    logger = logging.getLogger(__name__)
    logger.info("Get Session Day")
    logger.info(data)

    esd = experiment_session_days.objects.get(id=id)

    if esd.complete and esd.paypal_api:
        esd.pullPayPalResult(False)

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

    status = {"message":"", "info":[]}
    studentID = None

    try:
        if "=" in data["value"] and ";" in data["value"]:

            card_data = data["value"]
            card_data = card_data.replace(";", "=")
            card_data_list = card_data.split("=")

            studentID = int(card_data_list[1])
            logger.info(id)
        else:
            status["message"] = '<span style="color:red;font-weight: bold;">Card read error, invalid stripe data.</span>'
            logger.info("Stripe Reader Error, no equals or no semi colon")
    except:
        status["message"] = '<span style="color:red;font-weight: bold;">Card read error, invalid stripe data.</span>'
        logger.info("Stripe Reader card read error")

    if status["message"] == "":

        #if autoAddUser:
        esdu = getSubjectByID(id, studentID, request_user, False, "student_id")
        # else:
        #     esdu = getSubjectByID(id, studentID, request_user, True)

        logger.info(esdu)

        if len(esdu) > 1:
            status["message"] = "Error: Multiple users found"

            for u in esdu:
                status["info"].append(u.user.id)
            
            logger.info("Stripe Reader Error, multiple users found")
        else:
            if autoAddUser and request_user.is_staff and len(esdu)==0:
                #user not in session, add them
                status = autoAddSubject(studentID, id, request_user, ignoreConstraints)
                #status = r['status']
            elif autoAddUser and request_user.is_staff and len(esdu)==1:
                #user is in session confirm them
                esdu_first = esdu.first()
                esdu_first.confirmed = True
                esdu_first.save()

            if status["message"] == "":
                status["message"] = attendSubjectAction(esdu.first(), id, request_user)

    esd = experiment_session_days.objects.get(id=id)

    logger.info(status)

    return JsonResponse({"sessionDay" : esd.json_runInfo(request_user), "status": status}, safe=False)

#get subjects by student id or user id
def getSubjectByID(id, studentID, request_user, filter_confirmed, id_mode):

    esdu =  experiment_session_day_users.objects.filter(experiment_session_day__id=id) \
                                                .select_related('user')

    #search by student id or user id
    if id_mode == "student_id":
        esdu = esdu.filter(user__profile__studentID__icontains=studentID)
    elif id_mode == "recruiter_id":
        esdu = esdu.filter(user__id=studentID)
    else:
        esdu = esdu.filter(user__profile__public_id=studentID)

    if filter_confirmed:
        return esdu.filter(confirmed = True) 

    return esdu

def getProfileByID(studentID, request_user, id_mode):

    p = None

    #search by student id or user id
    if id_mode == "student_id":
        p = profile.objects.filter(studentID__icontains = studentID)
    elif id_mode == "recruiter_id":
        p = profile.objects.filter(user__id=studentID)
    else:
        p = profile.objects.filter(public_id=studentID)

    return p

#automatically add subject when during card swipe
def autoAddSubject(studentID, id, request_user, ignoreConstraints, upload_id_type="student_id"):
    logger = logging.getLogger(__name__)
    logger.info(f"Auto add subject: {studentID}")

    status = ""
    info = []

    p_list = getProfileByID(studentID, request_user, upload_id_type)
    esd = experiment_session_days.objects.get(id=id)

    if len(p_list) > 1:
        #multiple users found
        status = "Error, Multiple users found: "

        for u in p_list:
            status += f'{u.user.last_name}, {u.user.first_name} '
            info.append(u.user.id)

        logger.info(status)

    elif len(p_list) == 0:
        #no subject found
        status = f'<span style="color:red;font-weight: bold;">Error: No subject found with ID: {str(studentID)}</span>'
    else:
        #one subject found
        p = p_list.first()

        #check for recruitment violations
        r = json.loads(getManuallyAddSubject({"user":{"id":p.user.id},"sendInvitation":False},
                                             esd.experiment_session.id,
                                             request_user,
                                             ignoreConstraints,
                                             min_mode=True).content.decode("UTF-8"))
        if not "success" in r['status']:
            status = f'<span style="color:red;font-weight: bold;">Error: Could not add {p.user.last_name}, {p.user.first_name}: Recruitment Violation</span>'
            info.append(p.user.id)
        else:
            #confirm newly added user
            temp_esdu = esd.ESDU_b.filter(user__id=p.user.id).first()

            if not temp_esdu:
                status = f'<span style="color:red;font-weight: bold;">{p.user.last_name}, {p.user.first_name} could not be added to the session, try manual add.</span>'
                info.append(p.user.id)
            else:
                r = json.loads(changeConfirmationStatus({"userId":p.user.id,
                                                         "confirmed":"confirm",
                                                         "actionAll":False,
                                                         "esduId":temp_esdu.id},
                                                         esd.experiment_session.id,
                                                         ignoreConstraints,
                                                         min_mode=True).content.decode("UTF-8"))

                if not "success" in r['status']:
                    status = f"{p.user.last_name}, {p.user.first_name} added but manual confirmation is required."
                    info.append(p.user.id)
                    
    return {"message":status, "info":info}

#return paypal CSV
def getPayPalExport(data, id, request_user):
    '''
    export a PayPal formatted csv file for mass payment upload
    '''
    logger = logging.getLogger(__name__)
    logger.info("Pay Pal Export")
    logger.info(data)

    esd = experiment_session_days.objects.get(id=id)
    esdu = esd.ESDU_b.filter(Q(show_up_fee__gt = 0) | Q(earnings__gt = 0))

    esd.users_who_paypal_paysheet.add(request_user)
    esd.save()

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
    esdu = esd.ESDU_b.filter(attended=True).order_by('user__last_name', 'user__first_name')

    csv_response = HttpResponse(content_type='text/csv')
    csv_response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

    writer = csv.writer(csv_response)

    s=["Last Name", "First Name", "Email", "Student ID", "Recruiter ID", "Public ID", "Experiment Earnings", "On-Time Bonus", "Session Day ID"]
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

        esdu_attended = esd.ESDU_b.filter(attended=True)

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
        esd.ESDU_b.filter(attended=True) \
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

    esdu_list = []
    status = "success"

    for p in payoutList:
        #logger.info(p)
        esdu  = experiment_session_day_users.objects.filter(id = p['id']).first()

        if esdu:
            try:
                esdu.earnings = max(0, round(Decimal(p['earnings']), 2))
                esdu.show_up_fee = max(0, round(Decimal(p['showUpFee']), 2))
            except Exception  as e:
                logger.info("Background Save Error : ")
                logger.info(e)
                logger.info(p)
                esdu.earnings = Decimal("0")
                esdu.show_up_fee = Decimal("0")
                status = "fail"

            esdu_list.append(esdu)
        else:
            logger.info("Baground save error user not found")
            status = "fail"

    try:
        experiment_session_day_users.objects.bulk_update(esdu_list, ['earnings', 'show_up_fee'])
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
                esdu.earnings = max(0, round(Decimal(p['earnings']), 2))
                esdu.show_up_fee = max(0, round(Decimal(p['showUpFee']), 2))

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
        experiment_session_day_users.objects.bulk_update(esdu_list, ['earnings', 'show_up_fee'])
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
                esdu = esd.ESDU_b.all().filter(attended=False, bumped=False)
                esdu.update(earnings = 0, show_up_fee=0)

                esdu = esd.ESDU_b.all().filter(bumped=True)
                esdu.update(earnings = 0)


        json_info = esd.json_runInfo(request_user)
    except Exception  as exc:
        logger.warning(f"Fill earnings with fixed amount error : {exc}")
        status = "fail"

    return JsonResponse({"sessionDay" : json_info, "status":status}, safe=False)

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

    status = ""
    json_info = ""

    try:
        esd = experiment_session_days.objects.get(id=id)

        amount = data["amount"]

        esd.ESDU_b.filter(attended=True) \
                                            .update(earnings = Decimal(amount))

        status = "success"
        json_info = esd.json_runInfo(request_user)
    except Exception  as e:
        logger.info("Fill earnings with fixed amount error : ")
        logger.info(e)
        status = "fail"

    return JsonResponse({"sessionDay" : json_info, "status" : status}, safe=False)

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

        esd.ESDU_b.filter(Q(attended=True)|Q(bumped=True)) \
                                            .update(show_up_fee = showUpFee)

        #logger.info(esd.ESDU_b.filter(Q(attended=True)|Q(bumped=True)))

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

    if request_user.is_staff:
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

    status = ""

    #check subject session day exists
    if esdu:
        #check that subject has agreed to consent form
        if not esdu.user.profile.check_for_consent(esdu.experiment_session_day.experiment_session.consent_form):
            esdu.bumped = False
            esdu.attended = False

            status = f'<span style="color:red;font-weight: bold;">{esdu.user.last_name }, {esdu.user.first_name} must agree to the consent form.</span>'
            logger.info("Conset required:user" + str(esdu.user.id) + ", " + " ESDU: " + str(esdu.id))

        #check that subject has agreed to umbrella consent forms
        elif len(c:=esdu.user.profile.get_required_umbrella_consents()) > 0:
            esdu.bumped = False
            esdu.attended = False

            status = f'<span style="color:red;font-weight: bold;">{esdu.user.last_name }, {esdu.user.first_name} must agree to the umbrella form "{c[0]["display_name"]}".</span>'
            logger.info("Umbrella consent required:user" + str(esdu.user.id) + ", " + " ESDU: " + str(esdu.id))


        #check if user has confirmed for session
        elif not esdu.confirmed:
            esdu.attended = False
            esdu.bumped = False

            status = f'<span style="color:red;font-weight: bold;">{esdu.user.last_name}, {esdu.user.first_name} has not confirmed.</span>'
            logger.info("User has not confirmed:user" + str(esdu.user.id) + ", " + " ESDU: " + str(esdu.id))

        #backup check that subject has not already done this experiment if excluded
        elif esdu.getAlreadyAttended():
            esdu.attended = False
            esdu.bumped = True

            status = f'<span style="color:red;font-weight: bold;">{esdu.user.last_name}, {esdu.user.first_name} has already done this experiment.</span>'
            logger.info("Double experiment checkin attempt:user" + str(esdu.user.id) + ", " + " ESDU: " + str(esdu.id))

        #attend subject
        else:
            esdu.attended = True
            esdu.bumped = False

            status = esdu.user.last_name + ", " + esdu.user.first_name + " is now attending."

        esdu.save()
    else:
        status = f'<span style="color:red;font-weight: bold;">No subject found.</span>'

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
# def takeEarningsUpload(f, id, request_user, auto_add_subjects):
#     logger = logging.getLogger(__name__)
#     logger.info(f"Upload earnings file: auto add: {auto_add_subjects}")

#     #logger.info(f)

    
#     #request_user = request.user

#     #format incoming data
#     text = ""

#     for chunk in f.chunks():
#         text += str(chunk.decode("utf-8-sig"))

#     logger.info(text)

#     return takeEarningsUpload2(id, text, request_user, auto_add_subjects)

#process earnings upload
def takeEarningsUpload2(data, id, request_user):
    logger = logging.getLogger(__name__)
    logger.info(f"Upload earnings process text: id {id}, text {data}, {request_user}")

    text = data["text"]
    auto_add_subjects = data["autoAddUsers"]
    upload_id_type = data["uploadIdType"]

    message = ""

    esd = experiment_session_days.objects.get(id=id)

    try:

        #parse incoming file
        v=text.splitlines()

        for i in range(len(v)):
            v[i] = re.split(r',|\t',v[i])

            v_id = v[i][0]
            
            #convert to int if student id
            if upload_id_type == "student_id" or upload_id_type == "recruiter_id":            
                v[i][0] = int(v[i][0])

            #convert earnings to decimal
            v[i][1] = Decimal(v[i][1].replace('$',''))

            #bonus earnings
            if len(v[i]) > 2:
                v[i][2] = Decimal(v[i][2].replace('$',''))
            else:
                v[i].append(-1)
            
            #store orginally formmated Id
            v[i].append(v_id)

        logger.info(v)

        esdu_list = []
        u_list_valid = []

        #if adding subjects, get valid list
        if auto_add_subjects:
            u_list = {}
            if upload_id_type == "student_id":
                u_list = User.objects.filter(profile__studentID__in=[i[3] for i in v]).values('id')
            elif upload_id_type == "recruiter_id":
                u_list = User.objects.filter(id__in=[i[3] for i in v]).values('id')
            else:
                u_list = User.objects.filter(profile__public_id__in=[i[3] for i in v]).values('id')

            u_list_valid = list(esd.experiment_session.getValidUserList_forward_check(list(u_list),True,0,0,[],False,0))

        #store earnings
        for i in v:
            # if auto_add_subjects:
            #     esdu = getSubjectByID(id, i[0], request_user, False)
            # else:
            esdu = getSubjectByID(id, i[0], request_user, False, upload_id_type)

            # logger.info(esdu.count())

            m = ""

            if esdu.count() > 1:
                m = f'Error: More than one user found for ID {i[0]}<br>'
            elif esdu.count() == 0:
                #try to manually add user
                if request_user.is_staff and auto_add_subjects:
                    p = getProfileByID(i[0], request_user, upload_id_type)

                    if len(p) == 0:
                        value = {"message" : f"Error: Valid user not found ID: {i[0]}"}
                    elif len(p)>1:
                        value = {"message" : f"Error: More than one user found ID: {i[0]}"}
                    else:
                        if p.first().user in u_list_valid:
                            value = autoAddSubject(i[0], id, request_user, True, upload_id_type)
                        else:
                            value= {"message" : f"Error: Recruitment violation ID: {i[0]}"}

                    #if error add to return message
                    if value["message"] != "":
                        m = value["message"] + "<br>"

                    esdu = getSubjectByID(id, i[0], request_user, True, upload_id_type)
                else:
                    m = f'Error: No valid user found for ID {i[0]}<br>'

            if m.find("Error") == -1:
                if m != "":
                    message += str(m)

                #logger.info(esdu)
                esdu = esdu.first()

                #confirm user if auto add
                if request_user.is_staff and auto_add_subjects and esdu:
                    esdu.confirmed = True
                    esdu.save()

                m = attendSubjectAction(esdu, id, request_user)

                if m.find("is now attending") != -1:

                    esdu.earnings = max(0, Decimal(i[1]))
                    if i[2] != -1:
                        esdu.show_up_fee = max(0, Decimal(i[2]))

                    esdu_list.append(esdu)
                else:
                    message += str(m) + "<br>"
            else:
                message += str(m)

        if len(v) == 0:
            message = "Error: Empty list"

        logger.info(f'Earnings import list: {esdu_list}')
        experiment_session_day_users.objects.bulk_update(esdu_list, ['earnings', 'show_up_fee', 'attended'])
    except ValueError as e:
        message = f"Failed to load earnings: Invalid ID format"
        logger.info(message)
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

    for i in esd.ESDU_b.filter(attended=True):
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
    esdu_list = esd.ESDU_b.filter(Q(show_up_fee__gt=0) | Q(earnings__gt=0)) \
                          .filter(Q(attended=True) | Q(bumped=True))

    payments = []

    #build payments json
    for esdu in esdu_list:
        payments.append({"email": esdu.user.email, #, 'sb-8lqqw5080618@business.example.com'
                         "amount" : str(esdu.get_total_payout()),
                         "note" : f'{esdu.user.first_name}, {parm.paypal_email_body}',
                         "sender_item_id" : f'{esdu.id}',
                         "memo" : f"SD_ID: {esdu.experiment_session_day.id}, U_ID: {esdu.user.id}"})

    data = {}
    data["info"] = {"payment_id" : id_, #,random.randrange(0, 99999999)
                    "email_subject" : parm.paypal_email_subject}

    data["items"] = payments

    logger.info(f"PayPal API Payments: {data}")

    headers = {'Content-Type' : 'application/json', 'Accept' : 'application/json'}

    error_message = ""
    result = ""

    try:
        req = requests.post(f'{settings.PPMS_HOST}/payments/',
                            json=data,
                            auth=(str(settings.PPMS_USER_NAME), str(settings.PPMS_PASSWORD)),
                            headers=headers,
                            timeout=10)
    except requests.Timeout:
        error_message="Request to PayPal service timed out.  Check PayPal website for status."
        logger.error(f'payPalAPI error: {error_message}')
    except requests.ConnectionError:
        error_message="Could not connect to PayPal service."
        logger.error(f'payPalAPI error: {error_message}')

    if error_message=="":
        logger.info(f"PayPal API Payments: {req.json()}")

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
            esd.user_who_paypal_api = request_user
        
            for payment in req.json():
                result += f'<div>{payment["email"]}: ${float(payment["amount"]):0.2f}</div>'
                esd.paypal_api_batch_id = payment["payout_batch_id_paypal"]
            #result = req.json()
            esd.save()

    json_info = esd.json_runInfo(request_user)

    return JsonResponse({"result" : result,
                         "sessionDay" : json_info,
                         "error_message": error_message}, safe=False)
