import logging
from django_cron import CronJobBase, Schedule

class checkForReminderEmails(CronJobBase):
    RUN_EVERY_MINS = 1 # every 2 hours

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'main.check_for_recruitment_email_reminder'    # a unique code

    def do(self):
        logger = logging.getLogger(__name__)
        logger.info("Check for recruitment reminder emails")

    