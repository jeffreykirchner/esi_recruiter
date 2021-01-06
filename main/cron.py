import logging
from datetime import datetime,timedelta
import pytz
from main.models import experiment_session_days

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
        
        return {"standard": list(esd_list),"custom":list(esd_list2)}
