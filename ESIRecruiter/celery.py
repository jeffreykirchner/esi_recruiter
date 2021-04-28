from celery.schedules import crontab

import os
import logging

from celery import Celery

from django.conf import settings

import main

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ESIRecruiter.settings')

app = Celery('ESIRecruiter', include=['main.tasks'])

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    logger = logging.getLogger(__name__)
    logger.info("Setup periodic tasks")
    # sender.add_periodic_task(crontab(minute='*/5'), run_crons.s(), name='Run crons every 5 minutes')
    sender.add_periodic_task(300, run_crons.s(), name='Run crons every 5 minutes')

@app.task
def run_crons():

    cron_job = main.cron.checkForReminderEmails()
    cron_job.do()