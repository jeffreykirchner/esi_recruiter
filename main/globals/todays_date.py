'''
get todays tz adjusted info
'''
import pytz

from datetime import datetime

import main

#get todays, time zone adjusted date time object
def todays_date():
    '''
        Get today's server time zone adjusted date time object with zeroed time
    '''
    #logger = logging.getLogger(__name__)
    #logger.info("Get todays date object")

    prm = main.models.parameters.objects.first()
    tmz = pytz.timezone(prm.subjectTimeZone)

    d_today = datetime.now(tmz)
    d_today = d_today.replace(hour=0, minute=0, second=0, microsecond=0)       
    
    return d_today

def todays_time():
    '''
    get current tz adjusted time
    '''

    prm = main.models.parameters.objects.first()
    tmz = pytz.timezone(prm.experimentTimeZone)

    d_today = datetime.now(tmz)

    return d_today.time()


