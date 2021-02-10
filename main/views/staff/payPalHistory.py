'''
History of transanctions send to PayPal API.
'''
import json
import logging
from datetime import datetime,timedelta

import requests
import pytz

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import CharField, F, Value as V
from django.conf import settings

from main.decorators import user_is_staff

from main.models import parameters, help_docs

@login_required
@user_is_staff
def PayPalHistory(request):
    '''
    Handle incoming requestst
    '''

    if request.method == 'POST':

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getHistory":
            return get_history(request, data)

        return JsonResponse({"error" : "error"}, safe=False)

    #get
    try:
        help_text = help_docs.objects.annotate(rp=V(request.path, output_field=CharField()))\
                                     .filter(rp__icontains=F('path')).first().text

    except Exception as exce:
        help_text = "No help doc was found."

    param = parameters.objects.first()
    tmz = pytz.timezone(param.subjectTimeZone)
    d_today = datetime.now(tmz)
    d_one_year = d_today - timedelta(days=365)

    return render(request, 'staff/payPalHistory.html', {"helpText" : help_text,
                                                        "d_today" : d_today.date().strftime("%Y-%m-%d"),
                                                        "d_one_year" : d_one_year.date().strftime("%Y-%m-%d")})     

#return list of users based on search criterion
def get_history(request, data):
    '''
    Get the paypal history in the given range.
    '''
    logger = logging.getLogger(__name__)
    logger.info("PayPal History")
    logger.info(data)

    #request.session['userSearchTerm'] = data["searchInfo"]            
    history = []
    error_message = ""

    try:

        req = requests.get(f'{settings.PPMS_HOST}/payments/',
                           auth=(str(settings.PPMS_USER_NAME), str(settings.PPMS_PASSWORD)))

        #logger.info(r.status_code)

        if req.status_code != 200:
            error_message = req.json().get("detail")
        else:
            history = req.json()

            param = parameters.objects.first()
            tmz = pytz.timezone(param.subjectTimeZone)

            for hst in history:
                #convert earnings
                hst["amount"] = float(hst["amount"])
                hst["amount"] = f'${hst["amount"]:.2f}'

                #convert date
                hst["timestamp"] = datetime.strptime(hst["timestamp"], '%m/%d/%Y %H:%M:%S %Z')

                hst["timestamp"] = hst["timestamp"].astimezone(tmz).strftime("%#m/%#d/%Y %#I:%M %p")

    except Exception  as exce:
            logger.warning(f'PayPalHistory Error: {exce}')
            error_message = "Unable to retrieve history."

    return JsonResponse({"history" : history, "errorMessage":error_message}, safe=False)


