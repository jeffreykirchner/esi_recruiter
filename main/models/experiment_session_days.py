'''
Experiment Session Day Model
'''
from datetime import datetime
from datetime import timedelta
from decimal import Decimal

import logging
from unittest import result
import pytz
import requests

from django.db import models
from django.db.models.functions import Lower
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.db.models import Sum

import main

from main.models import experiment_sessions
from main.models import locations
from main.models import accounts
from main.models import parameters
from main.globals import send_mass_email_service

#one day of a session
class experiment_session_days(models.Model):
    '''
    Experiment Session Day Model
    '''
    experiment_session = models.ForeignKey(experiment_sessions, on_delete=models.CASCADE, related_name='ESD')
    location = models.ForeignKey(locations, on_delete=models.CASCADE)
    account = models.ForeignKey(accounts, on_delete=models.CASCADE)      #finanical account used to pay subjects from

    date = models.DateTimeField(default=now)                            #date and time of session
    length = models.IntegerField(default=60)                            #length of session in minutes
    date_end = models.DateTimeField(default=now)                        #date and time of session end, calculated from date and length
    enable_time = models.BooleanField(default=True)                     #if disabled, subject can do experiment at any time of day (online for example)

    auto_reminder = models.BooleanField(default=True)                   #send reminder emails to subject 24 hours before experiment
    reminder_time = models.DateTimeField(blank=True, null=True,
                                         default=None)                  #date and time that reminder email should be sent
    custom_reminder_time = models.BooleanField (default=False)          #set a custom reminder time
    reminder_email_sent = models.BooleanField(default=False)            #true once the reminder email is sent to subjects
    reminder_email_sent_count = models.IntegerField(blank=True, null=True) #number of reminder emails sent

    complete = models.BooleanField(default=False)                       #locks the session day once the user has pressed the complete button
    paypal_api = models.BooleanField(default=False)                     #true if the pay pal direct payment is used 
    paypal_api_batch_id = models.CharField(verbose_name="PayPal Batch Payout ID", max_length = 100, default="") 
    paypal_response = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)   #response from paypal after payment

    user_who_paypal_api = models.ForeignKey(User, on_delete=models.CASCADE, related_name='experiment_session_days_a', blank=True, null=True)       #user that pressed paypal api button
    users_who_paypal_paysheet = models.ManyToManyField(User, related_name='experiment_session_days_b', blank=True)  #users that pressed paypal paysheet
    users_who_printed_paysheet = models.ManyToManyField(User, related_name='experiment_session_days_d', blank=True) #users that printed paysheet
    users_who_printed_bumps = models.ManyToManyField(User, related_name='experiment_session_days_e', blank=True)    #users that printed bumpsheet

    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ID: {self.id}, Title: {self.experiment_session.experiment.title}"

    class Meta:
        verbose_name = 'Experiment Session Days'
        verbose_name_plural = 'Experiment Session Days'
        ordering = ['date']

    #get list of user and confirmed status
    def getListOfUserIDs(self):
        u_list=[]

        for u in self.ESDU_b.all():
            u_list.append({'user':u.user,'confirmed':u.confirmed})

        #u_list.sort()

        return u_list

    def checkUserInSession(self, check_user):
        return self.ESDU_b.filter(user=check_user).exists()

    #add user to session day
    def addUser(self, userID, staffUser, manuallyAdded):
        
        esdu = self.getNewUser(userID, staffUser, manuallyAdded)
        esdu.save()
    
    #return a new user to add
    def getNewUser(self, userID, staffUser, manuallyAdded):
        esdu = main.models.experiment_session_day_users()

        esdu.experiment_session_day = self
        esdu.user = User.objects.get(id=userID)
        esdu.addedByUser = staffUser
        esdu.manuallyAdded = manuallyAdded

        return esdu

    #sets up session day with defualt parameters
    def setup(self, es, u_list):
        self.experiment_session = es

        self.location = locations.objects.first()
        self.length = es.experiment.length_default
        self.account = es.experiment.account_default
        self.date = now()
        self.set_end_date()
        self.reminder_time = self.date - timedelta(days=1)

        self.save()

        #add list of session users if multiday
        for u in u_list:
            esdu = main.models.experiment_session_day_users()
            esdu.user = u['user']
            esdu.confirmed = u['confirmed']
            esdu.experiment_session_day = self
            esdu.save()

    #store end date
    def set_end_date(self):
        self.date_end = self.date + timedelta(minutes = self.length)
        self.save()

    #copy another session day's settings into this one
    def copy(self, esd):

        self.location = esd.location
        self.account = esd.account
        self.date = esd.date
        self.length = esd.length
        self.date_end  = esd.date_end
        self.auto_reminder = esd.auto_reminder
        self.reminder_time = esd.reminder_time
        self.enable_time = esd.enable_time
        self.custom_reminder_time = esd.custom_reminder_time

        self.save()

    #check if this session day can be deleted
    def allowDelete(self):

        # ESDU = self.ESDU_b.filter((Q(attended = 1) & (Q(earnings__gt = 0) | Q(show_up_fee__gt = 0))) |
        #                                                     (Q(bumped = 1) & Q(show_up_fee__gt = 0)))\
        #                                             .exists()

        ESDU = self.ESDU_b.filter(confirmed = True).exists()

        if ESDU:
            return False
        else:
            return True

    #get reminder time string
    def getReminderTimeString(self):
        p = parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)

        if not self.reminder_time:
            return "Not Set"
        else:
            return  self.reminder_time.astimezone(tz).strftime("%#m/%#d/%Y %#I:%M %p") + " " + p.subjectTimeZone

    #get user readable string of session date
    def getDateString(self):
        p = parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)
        if self.enable_time:
            return  self.date.astimezone(tz).strftime("%A %-m/%-d/%Y %-I:%M %p") + " " + p.subjectTimeZone
        else:
            return  self.date.astimezone(tz).strftime("%A %-m/%-d/%Y") + " Anytime " + p.subjectTimeZone
    
    #get html version of date string
    def getDateStringHTML(self):
        p = parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)

        v = self.date.astimezone(tz).strftime("%A") + "<br>"
        v += self.date.astimezone(tz).strftime("%-m/%-d/%Y") + "<br>"
        
        if self.enable_time:
            v += self.date.astimezone(tz).strftime("%-I:%M %p") + "-" +  self.date_end.astimezone(tz).strftime("%-I:%M %p") + " " + self.date.astimezone(tz).strftime("%Z") + "<br>"
        else:
            v +=  "Anytime" + "<br>"
        
        return v


    #get user readable string of session date with timezone offset
    def getDateStringTZOffset(self):
        p = parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)
        return  self.date.astimezone(tz).strftime("%#m/%#d/%Y %#I:%M %p %z")
    
    def getDateStringTZOffsetInput(self):
        p = parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)
        return  self.date.astimezone(tz).strftime("%Y-%m-%dT%H:%M")

    #get the local time of experiment start
    def getStartTimeString(self):
        p = parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)
        return  self.date.astimezone(tz).strftime("%-I:%M %p")

    #get the local time of experiment end
    def getEndTimeString(self):
        p = parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)
        endTime = self.date + timedelta(minutes = self.length)
        return  endTime.astimezone(tz).strftime("%-I:%M %p")

    #hours until start
    def hoursUntilStart(self):
        #time remaining until start
        d_now = datetime.now(pytz.utc)
        timeRemaining = self.date - d_now

        return timeRemaining.total_seconds()/60/60
        #return str(timeRemaining)
    
    #hours until start in html format
    def hoursUntilStartHTML(self):
        #time remaining until start
        time_until_start = self.hoursUntilStart()
        hours_until_start = int(time_until_start)
        minutes_until_start = int(time_until_start %1 * 60)

        v = ""

        if hours_until_start > 0:
            if hours_until_start == 1:
                v += str(hours_until_start) + " hr "
            else:
                 v += str(hours_until_start) + " hrs "
        if minutes_until_start > 0:
            if minutes_until_start == 1:
                v += str(minutes_until_start) + " min"
            else:
                v += str(minutes_until_start) + " mins"
        
        return v

    #get a list of session who's room and time overlap this one
    def getRoomOverlap(self):
        '''
        get any room overlaps for this session day
        '''
        if self.enable_time:
            esd = main.models.experiment_session_days.objects.filter(location=self.location)\
                                                         .filter(date__lte=self.date_end)\
                                                         .filter(date_end__gte=self.date)\
                                                         .exclude(enable_time=False)\
                                                         .exclude(experiment_session__canceled = True)\
                                                         .exclude(id=self.id)
            return [i.json_min() for i in esd]

        return []

    #get user readable string of session lengths in mintues
    def getLengthString(self):

        #return str(self.length) + " minutes"
        return main.globals.format_minutes(self.length)

    #build an reminder email given the experiment session
    def getReminderEmail(self):
        #logger = logging.getLogger(__name__)

        p = parameters.objects.first()

        message = ""

        message = self.experiment_session.experiment.reminderText

        message = message.replace("[session length]", self.getLengthString())
        message = message.replace("[session date and time]", self.getDateString())
        message = message.replace("[on time bonus]", "$" + self.experiment_session.experiment.getShowUpFeeString())
        message = message.replace("[contact email]", p.labManager.email)
        message = message.replace("[session id]", str(self.experiment_session.id))

        return message

    #send a reminder email to all subjects in session day
    def sendReminderEmail(self):
        logger = logging.getLogger(__name__)

        #don't send remind if it has already been sent
        if self.reminder_email_sent:
            logger.warning(f"Send Reminder emails error already sent: session {self.experiment_session}, session day {self.id}")
            return {"emailList": [], "status":"fail"}

        #don't send reminder if session canceled
        if self.experiment_session.canceled:
            logger.warning(f"Send Reminder emails error session canceled: session {self.experiment_session}, session day {self.id}")
            return {"emailList": [], "status":"fail"}

        self.reminder_email_sent = True
        self.save()

        p = parameters.objects.first()
        logger.info(f"Send Reminder emails to: session {self.experiment_session}, session day {self.id}")

        users_list = self.ESDU_b.filter(confirmed=True).select_related("user")

        if len(users_list) == 0:
            logger.info(f"No confirmed users for session {self.experiment_session}")
            return {"emailList": users_list, "status":"success"}

        logger.info(users_list)
        user_list = []

        for i in users_list:
            user_list.append({'email':i.user.email,
                              'variables':[{"name" : "first name", "text" : i.user.first_name},
                                           {"name" : "last name", "text" : i.user.last_name},
                                           {"name" : "email", "text" : i.user.email},
                                           {"name" : "recruiter id", "text" : str(i.user.id)},
                                           {"name" : "student id", "text" : i.user.profile.studentID},
                                          ]
                             })

        logger.info(user_list)

        memo = f"Send reminders for session day: {self.id}"

        reminder_text = self.getReminderEmail()

        mail_result = send_mass_email_service(user_list,
                                              p.reminderTextSubject.replace("[session date and time]",self.experiment_session.getSessionDayDateString()), 
                                              reminder_text, 
                                              reminder_text, 
                                              memo, 
                                              len(users_list) * 2)
        logger.info(mail_result)

        #store the number of reminders sent
        self.reminder_email_sent_count = mail_result.get("mail_count", 0)
        self.save()

        return {"emailList": users_list, "status":"success"}

    #return true if re-opening is allowed
    def reopenAllowed(self, u):

        if not self.complete or u.is_staff:
            return True
        else:
            td = datetime.now(pytz.UTC) - self.date

            if td>timedelta(days=1):
                return False
            else:
                return True

    #convert input into comma dilimited string
    def convertToCommaString(self, in_str):
        converted_list = [element.get_full_name() for element in in_str]
        return ", ".join(converted_list)

    #upate paypal batch id from paypal service memo text
    def updatePayPalBatchIDFromMemo(self):

        logger = logging.getLogger(__name__)

        headers = {'Content-Type' : 'application/json', 'Accept' : 'application/json'}

        req = requests.get(f'{settings.PPMS_HOST}/payments/memo_search/{self.id}/',
                           auth=(str(settings.PPMS_USER_NAME), 
                                 str(settings.PPMS_PASSWORD)),
                           timeout=10)
        
        if len(req.json())>0:

            for i in req.json():
                self.paypal_api_batch_id = i.get('payout_batch_id_paypal', 'No Batch ID')
                self.save()

                logger.info(f'updatePayPalBatchIDFromMemo: ESD ID:{self.id}, payout_batch_id_paypal: {self.paypal_api_batch_id}')
                break

        else:
            logger.warning(f'updatePayPalBatchIDFromMemo: ESD ID:{self.id}, payout_batch_id_paypal: Not Found')

    #pull paypal batch payment status from PayPal API
    def pullPayPalResult(self, force_pull):
        logger = logging.getLogger(__name__)

        if not self.complete or not self.paypal_api:
            return

        if self.paypal_api_batch_id == "":
            logger.error(f'pullPayPalResult: ESD ID:{self.id}, payout_batch_id_paypal: Not Found')
            return
        
        if not force_pull and self.paypal_response:
            if self.paypal_response.get("batch_status","not found") == "SUCCESS":
                if not self.ESDU_b.filter(Q(paypal_response__transaction_status = "PENDING") | 
                                          Q(paypal_response__transaction_status = "UNCLAIMED") |
                                          #Q(paypal_response__transaction_status = "RETURNED") |
                                          Q(paypal_response__transaction_status = "ONHOLD")).exists():
                    #logger.info(f'pullPayPalResult: ESD ID:{self.id}, no pull needed.')
                    return
                                        


        headers = {'Content-Type' : 'application/json', 'Accept' : 'application/json'}

        try:
            req = requests.get(f'{settings.PPMS_HOST}/payments/get_batch_status/{self.paypal_api_batch_id}/',
                                auth=(str(settings.PPMS_USER_NAME), 
                                      str(settings.PPMS_PASSWORD)),
                                timeout=10)
        except requests.Timeout:
            logger.error(f'pullPayPalResult error: service timed out, ESD ID:{self.id}')
            return
        except requests.ConnectionError:
            logger.error(f'pullPayPalResult error: Could not connect, ESD ID:{self.id}')
            return

        if len(req.json())>0:

            req_json = req.json()

            if not req_json.get("batch_header", False):
                logger.error(f'pullPayPalResult: ESD ID:{self.id}, status not found: Not Found')
                self.paypal_response=None
                self.save()
                return

            #store header in esd
            self.paypal_response = req_json["batch_header"]
            self.save()

            #store items in esdu
            #self.ESDU_b.all().update(paypal_response=None)
            self.ESDU_b.filter(Q(attended=True) | Q(bumped=True)).update(paypal_response= {'transaction_status':'NOT_FOUND', 
                                                       'transaction_id':'none', 
                                                       'errors':{'message':'Transaction not found on PayPal server', 'name':'Not Found'},
                                                       'payout_item': {'recipient_type': 'EMAIL', 'amount': {'currency': 'USD', 'value': '0'}},
                                                       'payout_item_fee': {'currency': 'USD', 'value': '0.0'}})

            esdu_list = []
            for i in req_json.get("items", []):   
                sender_item_id = i['payout_item']['sender_item_id'] 
                sender_item_id=sender_item_id.split('_')[-1]
                esdu  = self.ESDU_b.filter(Q(user__email = i['payout_item']['receiver']) | 
                                           Q(id=sender_item_id)).first()

                if not esdu:
                    logger.error(f'pullPayPalResult: ESD ID:{self.id}, subject not found: {i}')
                else:
                    esdu.paypal_response = i
                    esdu_list.append(esdu)
            
            if len(esdu_list)>0:
                main.models.experiment_session_day_users.objects.bulk_update(esdu_list, ['paypal_response'])

        else:
            logger.error(f'pullPayPalResult: ESD ID:{self.id}, status not found: Not Found')

    #return paypal fees and totals for successful payments
    def get_paypal_realized_totals(self):
        logger = logging.getLogger(__name__)

        result = {"realized_fees":0, "realized_payouts":0}

        if not self.complete or not self.paypal_api:
            result
    
        payouts =  self.ESDU_b.filter(paypal_response__isnull=False) \
                              .filter(paypal_response__transaction_status="SUCCESS")\
                              .values_list('paypal_response__payout_item__amount__value',flat=True)
        
        fees =  self.ESDU_b.filter(paypal_response__isnull=False) \
                           .filter(paypal_response__transaction_status="SUCCESS")\
                           .values_list('paypal_response__payout_item_fee__value',flat=True)

        payouts_unclaimed =  self.ESDU_b.filter(paypal_response__isnull=False) \
                                 .filter(paypal_response__transaction_status="UNCLAIMED")\
                                 .values_list('paypal_response__payout_item__amount__value',flat=True)
        
        fees_unclaimed =  self.ESDU_b.filter(paypal_response__isnull=False) \
                              .filter(paypal_response__transaction_status="UNCLAIMED")\
                              .values_list('paypal_response__payout_item_fee__value',flat=True)

        result['realized_fees'] = sum(map(lambda n:Decimal(n), fees))
        result['realized_payouts'] = sum(map(lambda n:Decimal(n), payouts))
        result['unclaimed'] = sum(map(lambda n:Decimal(n), payouts_unclaimed)) + sum(map(lambda n:Decimal(n), fees_unclaimed))

        # logger.info(f'get_paypal_realized_totals: {result}')

        payouts =  self.ESDU_b.filter(paypal_response__isnull=False) \
                              .filter(user__profile__international_student=True) \
                              .filter(paypal_response__transaction_status="SUCCESS")\
                              .values_list('paypal_response__payout_item__amount__value',flat=True)
        
        fees =  self.ESDU_b.filter(paypal_response__isnull=False) \
                           .filter(user__profile__international_student=True) \
                           .filter(paypal_response__transaction_status="SUCCESS")\
                           .values_list('paypal_response__payout_item_fee__value',flat=True)

        result['realized_fees_international']=sum(map(lambda n:Decimal(n), fees))
        result['realized_payouts_international']=sum(map(lambda n:Decimal(n), payouts))

        logger.info(f'get_paypal_realized_totals: {result}')

        return result
    
    #return the sum of payments paid to the subjects
    def get_cash_payout_total(self):
        logger = logging.getLogger(__name__)
        
        payouts = self.ESDU_b.filter(Q(attended=True) | Q(bumped=True)) \
                              .aggregate(show_up_fee=Sum('show_up_fee'), 
                                         earnings=Sum('earnings'))

        # logger.info(f'get_cash_payout_total: {payouts}')

        result = {'show_up_fee' : payouts['show_up_fee'], 'earnings' : payouts['earnings']}

        payouts_2 = self.ESDU_b.filter(Q(attended=True) | Q(bumped=True)) \
                             .filter(user__profile__international_student=True) \
                             .aggregate(show_up_fee=Sum('show_up_fee'), 
                                         earnings=Sum('earnings'))
        
        result['show_up_fee_international'] = payouts_2['show_up_fee']
        result['earnings_international'] = payouts_2['earnings']

        # logger.info(f'get_cash_payout_total: {payouts_2}')

        return result

    #get small json object
    def json_min(self):
        confirmedCount = self.ESDU_b.filter(confirmed=True).count()
        attendedCount = self.ESDU_b.filter(attended=True).count()
        totalCount = self.ESDU_b.count()

        return{
            "id":self.id,
            "date":self.date,
            "name":self.experiment_session.experiment.title,
            "session_id":self.experiment_session.id,
            "confirmedCount": confirmedCount,
            "attendedCount": attendedCount,
            "totalCount": totalCount,
            "enable_time":self.enable_time,
        }

    #info to send to session run page
    def json_runInfo(self, u):
        '''
        u:User
        '''

        is_during_session = False           #while session is taking place

        if self.enable_time:
            if datetime.now(pytz.UTC) >= self.date - timedelta(hours=2) and \
                datetime.now(pytz.UTC) <= self.date_end + timedelta(hours=2) :

                is_during_session = True
        else:
            if datetime.now(pytz.UTC) >= self.date - timedelta(hours=24) and \
               datetime.now(pytz.UTC) <= self.date_end + timedelta(hours=24) :

                is_during_session = True

        return{
            "id":self.id,
            "location":self.location.json(),
            "date":self.getDateString(),
            "date_raw":self.date,
            "reminder_time":self.getReminderTimeString(),
            "reminder_time_raw":self.reminder_time,
            "custom_reminder_time":self.custom_reminder_time,
            "length":self.length,
            "experiment_session_days_user" : self.json_runInfoUserList(),
            "defaultShowUpFee": f'{self.experiment_session.experiment.showUpFee:.2f}',
            "complete":self.complete,
            "canceled":self.experiment_session.canceled,
            "enable_time":self.enable_time,
            "confirmedCount": self.ESDU_b.filter(confirmed=True).count(),
            "attendingCount" : self.ESDU_b.filter(attended=True).count(),
            "requiredCount" : self.experiment_session.recruitment_params.actual_participants,
            "bumpCount" : self.ESDU_b.filter(bumped=True).count(),
            "reopenAllowed" : self.reopenAllowed(u),
            "paypalAPI":self.paypal_api,
            "paypal_response":self.paypal_response,
            "paypal_realized_totals":self.get_paypal_realized_totals(),
            "is_during_session" : is_during_session,
            "user_who_paypal_api" :  self.user_who_paypal_api.get_full_name() if self.user_who_paypal_api else "---",
            "users_who_paypal_paysheet" : self.convertToCommaString(self.users_who_paypal_paysheet.all()) if len(self.users_who_paypal_paysheet.all()) != 0 else "---",
            "users_who_printed_paysheet" : self.convertToCommaString(self.users_who_printed_paysheet.all()) if len(self.users_who_printed_paysheet.all()) != 0 else "---",
            "users_who_printed_bumps" : self.convertToCommaString(self.users_who_printed_bumps.all()) if len(self.users_who_printed_bumps.all()) != 0 else "---",
        }

    #json info for run session
    def json_runInfoUserList(self):
        u_list_c = self.ESDU_b.\
                       filter(confirmed=True).\
                       order_by(Lower('user__last_name'),Lower('user__first_name'))

        return [i.json_runInfo() for i in u_list_c]

    #json object of model
    def json(self, getUnconfirmed):

        logger = logging.getLogger(__name__)
        logger.info("Experiment Session Days JSON")
        logger.info(f"Get un-confirmed: {getUnconfirmed}")

        u_list_c = self.ESDU_b.\
                       filter(confirmed=True).\
                       select_related('user').\
                       order_by(Lower('user__last_name'), Lower('user__first_name'))

        u_list_u = self.ESDU_b.\
                       filter(confirmed=False).\
                       select_related('user').\
                       order_by(Lower('user__last_name'), Lower('user__first_name'))

        attendedCount = self.ESDU_b.filter(attended=True).count()
        
        u_list_u_json =[]


        if getUnconfirmed:

            #get list of valid users
            u_list_u2_json = [{"id" : i.user.id} for i in u_list_u]

            user_list_valid_clean = []
            if u_list_u2_json != []:
                user_list_valid_clean = self.experiment_session.getValidUserList_forward_check(u_list_u2_json,False,0,0,[],False,len(u_list_u2_json))

            #logger.info()
            logger.info(f'Valid list session day {self.id}, {user_list_valid_clean}')

            u_list_u_json = [{"id":i.id,
                              "confirmed":i.bumped,
                              "user":{"id" : i.user.id,
                                      "first_name":i.user.first_name.capitalize(),
                                      "last_name":i.user.last_name.capitalize(),},
                              "allowDelete" : i.allowDelete(),
                              "allowConfirm" : i.allowConfirm(),
                              "alreadyAttending":i.getAlreadyAttended(),
                              "valid" :  0}
                            for i in u_list_u]

            #mark users that do not violate recruitment parameters
            for u in u_list_u_json:
                for uv in user_list_valid_clean:
                    if u['user']['id'] == uv.id:
                        u['valid'] = 1
                        break

        return{
            "id":self.id,
            "location":self.location.id,
            "date":self.getDateString(),
            "date_raw":self.date,
            "reminder_time":self.getReminderTimeString(),
            "reminder_time_raw":self.reminder_time,
            "custom_reminder_time":self.custom_reminder_time,
            "reminder_email_sent":self.reminder_email_sent,
            "reminder_email_sent_count":self.reminder_email_sent_count,
            "length":self.length,
            "account":self.account.id,
            "auto_reminder":self.auto_reminder,
            "enable_time":self.enable_time,
            "experiment_session_days_user" : [{"id":i.id,
                                               "confirmed":i.bumped,
                                               "user":{"id" : i.user.id,
                                                        "first_name":i.user.first_name.capitalize(),
                                                        "last_name":i.user.last_name.capitalize(),},
                                               "allowDelete" : i.allowDelete(),
                                               "alreadyAttending":i.getAlreadyAttended(),
                                               "allowConfirm" : i.allowConfirm(),}
                                             for i in u_list_c],

            "experiment_session_days_user_unconfirmed" : u_list_u_json,
            "confirmedCount": len(u_list_c),
            "attendedCount" : attendedCount,
            "unConfirmedCount": len(u_list_u),
            "roomOverlap":self.getRoomOverlap(),
            "allowDelete":self.allowDelete(),
            "complete":self.complete,
            "paypalAPI":self.paypal_api,
        }

    def json_paypal_history_info(self):
        hold_list = self.ESDU_b.exclude(paypal_response__transaction_status="SUCCESS") \
                               .exclude(paypal_response=None) \
                               .values('user__id', 
                                       'user__last_name', 
                                       'user__first_name', 
                                       'paypal_response')

        return{
            "id":self.id,
            "date":self.getDateString(),
            "title":self.experiment_session.experiment.title,
            "paypal_response":self.paypal_response,
            "hold_list" : list(hold_list),
            "realized_totals":self.get_paypal_realized_totals(),
        }
