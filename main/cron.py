import logging
import pytz

from datetime import datetime,timedelta

from django.contrib.auth.models import User
from django.utils.html import strip_tags
from django.template.loader import get_template
from django.template import Context

from main.models import experiment_session_days
from main.models import DailyEmailReport

from main.globals import send_daily_report
from main.globals import todays_date

from main.views import get_paypal_history_list

class checkForReminderEmails():


    def do(self):
        logger = logging.getLogger(__name__)
        logger.info("Check for recruitment reminder emails")

        #send reminder if experiment is between 20 and 24 hours out
        t_now_plus_24 = datetime.now(pytz.UTC) + timedelta(hours=24)
        t_now_plus_20 = datetime.now(pytz.UTC) + timedelta(hours=20)

        esd_list = experiment_session_days.objects.filter(date__lte = t_now_plus_24,
                                                          date__gte = t_now_plus_20,
                                                          reminder_email_sent = False,
                                                          experiment_session__canceled = False,
                                                          auto_reminder = True,
                                                          custom_reminder_time = False)      
                                                          
         
        logger.info(f"Standard reminder: {esd_list}")

        if len(esd_list) == 0:
            logger.info("No standard reminders sent")
        else:              
            for e in esd_list:
                e.sendReminderEmail()

        #custom reminder times        
        t_now = datetime.now(pytz.UTC)
        t_minus_4 = datetime.now(pytz.UTC) - timedelta(hours=4)

        esd_list2 = experiment_session_days.objects.filter(reminder_time__lte = t_now,
                                                          reminder_time__gte = t_minus_4,
                                                          reminder_email_sent = False,
                                                          experiment_session__canceled = False,
                                                          auto_reminder = True,
                                                          custom_reminder_time = True)

        logger.info(f"Custom reminder: {esd_list2}")

        if len(esd_list2) == 0:
            logger.info("No custom reminders sent")
        else:              
            for e in esd_list2:
                e.sendReminderEmail()
        
        return {"standard": list(esd_list), "custom":list(esd_list2)}

def check_send_daily_report_email():
    '''
    send a daily email to specifed users
    '''

    logger = logging.getLogger(__name__)
    logger.info("Send daily report")

    status = ""
    
    today = todays_date()

    daily_email_report = DailyEmailReport.objects.filter(date__day=today.day) \
                                                 .filter(date__month=today.month) \
                                                 .filter(date__year=today.year)

    if len(daily_email_report) > 0:
        return "Report has already been sent today"

    today -= timedelta(days=1)

    #test code
    #start_day = today - timedelta(days=365)
    start_day = today 

    paypal_history_list = get_paypal_history_list(start_day.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))
    
    daily_email_report = DailyEmailReport()

    #html version from template
    daily_email_report.text = get_template('email/daily_report.html').render({ 'report_date': today.strftime('%m/%d/%Y'),
                                                                               'error_message':paypal_history_list["error_message"],
                                                                               'payments' : paypal_history_list["history"] })
        
    #plain text version
    plain_text = f"*** PayPal report for {today.strftime('%m/%d/%Y')}***\n\n"

    if paypal_history_list["error_message"] == "":
        if len(paypal_history_list["history"]) == 0:
            plain_text += f"---No payments today---\n"
        else:
            for h in paypal_history_list["history"]:
                plain_text += f"{h['email']}: {h['amount']}\n"
    else:
        plain_text += f"Report Error: {paypal_history_list['error_message']}"
    
    daily_email_report.save()

    user_list = User.objects.filter(profile__type=1) \
                            .filter(profile__send_daily_email_report=True)

    

    return send_daily_report(user_list, plain_text, daily_email_report.text)
