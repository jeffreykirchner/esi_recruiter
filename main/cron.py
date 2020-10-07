import logging
from django_cron import CronJobBase, Schedule
from datetime import datetime,timedelta
import pytz
from main.models import experiment_session_days

class checkForReminderEmails(CronJobBase):
    RUN_EVERY_MINS = 1 

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'main.check_for_recruitment_email_reminder'    # a unique code

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
                                                          auto_reminder = True)      
                                                          
        logger.info(esd_list) 
        
        if len(esd_list) == 0:
            logger.info("None Found")
        else:            
            for e in esd_list:
                e.sendReminderEmail()
        
        return esd_list
