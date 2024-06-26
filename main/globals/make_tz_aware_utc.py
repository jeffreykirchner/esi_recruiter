'''
take date and return timezone aware datetime in UTC
'''
from datetime import datetime

import logging
import pytz

from main.models import Parameters

def make_tz_aware_utc(old_date, new_hour, new_min, new_sec):
    '''
    take date and return timezone aware datetime in UTC
    '''
    logger = logging.getLogger(__name__)
    logger.info(f"make_tz_aware_utc start date: {old_date}")

    parm = Parameters.objects.first()
    tmz = pytz.timezone(parm.subjectTimeZone)

    new_date = datetime.now(tmz)
    new_date = new_date.replace(day=old_date.day, month=old_date.month, year=old_date.year)
    new_date = new_date.replace(hour=new_hour, minute=new_min, second=new_sec, microsecond=0)

    new_date = new_date.astimezone(pytz.timezone('UTC'))

    logger.info(f"make_tz_aware_utc new date: {new_date}")

    return new_date





