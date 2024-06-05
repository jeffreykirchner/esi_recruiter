'''
History of transanctions send to PayPal API.
'''
from decimal import Decimal
from datetime import datetime, timedelta

import json
import logging
import requests
import pytz
import csv
import io

from requests.utils import quote

from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import CharField, F, Value as V
from django.conf import settings
from django.views import View
from django.utils.decorators import method_decorator

from main.decorators import user_is_staff

from main.models import parameters
from main.models import help_docs
from main.models import experiment_session_days
from main.models import profile
from main.models import accounts

from main.forms import ExpenditureReportForm

from main.globals import gross_up

class PaymentHistory(View):
    '''
    show history of payments overs specified time range
    '''

    template_name = "staff/payment_history.html"

    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    #@method_decorator(staff_member_required)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logger = logging.getLogger(__name__)

        try:
            help_text = help_docs.objects.annotate(rp=V(request.path, output_field=CharField()))\
                                        .filter(rp__icontains=F('path')).first().text

        except Exception as exce:
            help_text = "No help doc was found."

        param = parameters.objects.first()
        tmz = pytz.timezone(param.subjectTimeZone)
        d_today = datetime.now(tmz)
        d_one_day = d_today - timedelta(days=1)
        d_one_month = d_today - timedelta(days=30)

        #start of fiscal year
        d_fisical_start = d_today
        d_fisical_start = d_fisical_start.replace(month=6, day=1)

        if d_today.month<6:
            d_fisical_start = d_fisical_start.replace(year=d_fisical_start.year-1)

        expenditure_report_form = ExpenditureReportForm()
        expenditure_report_form_ids=[]
        for i in expenditure_report_form:
            expenditure_report_form_ids.append(i.html_name)

        return render(request, self.template_name, {"helpText" : help_text,
                                                    "expenditure_report_form" : expenditure_report_form,
                                                    "expenditure_report_form_ids" : expenditure_report_form_ids,
                                                    "d_today" : d_today.date().strftime("%Y-%m-%d"),
                                                    "d_one_day" : d_one_day.date().strftime("%Y-%m-%d"),
                                                    "d_one_month" : d_one_month.date().strftime("%Y-%m-%d"),
                                                    "d_fisical_start" : d_fisical_start.date().strftime("%Y-%m-%d")}) 
    
    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    #@method_decorator(staff_member_required)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__) 

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getHistory":
            return get_history(request, data)
        elif data["action"] == "getHistoryRecruiter":
            return get_paypal_history_recruiter(request, data)
        elif data["action"] == "getHistoryBudget":
            return get_budget_history(request, data)
        elif data["action"] == "downloadHistoryBudget":
            return get_budget_history(request, data)
            
        return JsonResponse({"error" : "error"}, safe=False)

def get_history(request, data):
    '''
    Get the paypal history in the given range.
    '''
    logger = logging.getLogger(__name__)
    logger.info(f"PayPal History {data}")

    start_date = datetime.strptime(data["startDate"], "%Y-%m-%d").date()
    end_date = datetime.strptime(data["endDate"], "%Y-%m-%d").date()

    range_delta = end_date - start_date
    if range_delta.days > 365:
        return JsonResponse({"history" : [], 
                            "errorMessage" : "The range cannot exceed one year."}, safe=False)

    #request.session['userSearchTerm'] = data["searchInfo"]            
    history = get_paypal_history_list(data["startDate"], data["endDate"])

    return JsonResponse({"history" : history['history'], "errorMessage":history['error_message']}, safe=False)

def get_paypal_history_list(start_date, end_date):
    '''
    return a formated list of paypal payments over the specficed date range
    date format YYYY-MM-DD

    '''
    logger = logging.getLogger(__name__)

    history = []
    error_message = ""

    param = parameters.objects.first()
    tmz = pytz.timezone(param.subjectTimeZone)

    try:

        #convert dates to UTC
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        range_delta = end_date - start_date
        if range_delta.days > 365:
            return JsonResponse({"history" : [], 
                                "errorMessage" : "The range cannot exceed one year."}, safe=False)

        # start_date = make_tz_aware_utc(start_date, 0, 0, 0).date()
        # end_date = make_tz_aware_utc(end_date, 23, 59, 59).date()

        subject_time_zone_safe = quote(param.subjectTimeZone, safe='')

        req = requests.get(f'{settings.PPMS_HOST}/payments/{start_date}/{end_date}/{subject_time_zone_safe}',
                           auth=(str(settings.PPMS_USER_NAME), str(settings.PPMS_PASSWORD)),
                           timeout=30)

        #logger.info(r.status_code)

        if req.status_code != 200:
            error_message = req.json().get("detail")
        else:
            history = req.json()            

            for hst in history:
                #convert earnings
                hst["amount"] = float(hst["amount"])
                hst["amount"] = f'${hst["amount"]:.2f}'

                #convert date
                hst["timestamp"] = datetime.strptime(hst["timestamp"], '%m/%d/%Y %H:%M:%S %Z')
                hst["timestamp"] = hst["timestamp"].astimezone(tmz).strftime("%#m/%#d/%Y %#I:%M %p")

    except Exception  as exce:
            logger.warning(f'PaymentHistory Error: {exce}')
            error_message = "Unable to retrieve history."
    
    return {'history' : history, 'error_message' : error_message}

def get_paypal_history_recruiter(request, data):
    '''
    return a formated list of paypal payments over the specficed date range from recruiter
    date format YYYY-MM-DD
    '''

    logger = logging.getLogger(__name__)
    logger.info(f"PayPal History recruiter {data}")

    history = []
    error_message = ""

    param = parameters.objects.first()
    tz = pytz.timezone(param.subjectTimeZone)

    # try:
    s_date = datetime.now(tz)
    e_date = datetime.now(tz)

    s_date_start = datetime.strptime(data["startDate"], "%Y-%m-%d").date() 
    e_date_start = datetime.strptime(data["endDate"], "%Y-%m-%d").date() 

    range_delta = e_date_start - s_date_start
    if range_delta.days > 365:
        return JsonResponse({"history" : [], 
                             "errorMessage" : "The range cannot exceed one year."}, safe=False)

    s_date = s_date.replace(day=s_date_start.day,month=s_date_start.month, year=s_date_start.year)
    e_date = e_date.replace(day=e_date_start.day,month=e_date_start.month, year=e_date_start.year)

    s_date = s_date.replace(hour=0,minute=0, second=0)
    e_date = e_date.replace(hour=23,minute=59, second=59)

    logger.info(s_date)
    logger.info(e_date) 

    esd_list=[]
    esd_qs = experiment_session_days.objects.filter(date__gte=s_date) \
                                                .filter(date__lte=e_date) \
                                                .filter(paypal_api=True) \
                                                .filter(complete=True)

    for i in esd_qs:
        i.pullPayPalResult(False)   

    esd_qs = experiment_session_days.objects.filter(date__gte=s_date) \
                                            .filter(date__lte=e_date) \
                                            .filter(paypal_api=True) \
                                            .filter(complete=True) \
                                            .order_by('-date')

    history = []
    for i in esd_qs:
        history.append(i.json_paypal_history_info())

    # except Exception  as exce:
    #         logger.warning(f'PaymentHistory Error: {exce}')
    #         error_message = "Unable to retrieve history."
    
    return JsonResponse({"history" : history, 
                         "errorMessage":error_message}, safe=False)

def get_budget_history(request, data):
    '''
    return expenditures for each budget across the specified date range
    date format YYYY-MM-DD
    '''

    logger = logging.getLogger(__name__)
    logger.info(f"Budget History {data}")

    history = []
    error_message = ""

    param = parameters.objects.first()
    tz = pytz.timezone(param.subjectTimeZone)

    # try:
    s_date = datetime.now(tz)
    e_date = datetime.now(tz)

    s_date_start = datetime.strptime(data["startDate"], "%Y-%m-%d").date() 
    e_date_start = datetime.strptime(data["endDate"], "%Y-%m-%d").date() 

    #range should not exceed 365 days
    range_delta = e_date_start - s_date_start
    if range_delta.days > 365:
        return JsonResponse({"history" : [], 
                             "errorMessage" : "The range cannot exceed one year."}, safe=False)

    s_date = s_date.replace(day=s_date_start.day,month=s_date_start.month, year=s_date_start.year)
    e_date = e_date.replace(day=e_date_start.day,month=e_date_start.month, year=e_date_start.year)

    s_date = s_date.replace(hour=0,minute=0, second=0)
    e_date = e_date.replace(hour=23,minute=59, second=59)

    logger.info(s_date)
    logger.info(e_date) 

    #pull current paypal history
    esd_qs = experiment_session_days.objects.filter(date__gte=s_date) \
                                                .filter(date__lte=e_date) \
                                                .filter(paypal_api=True) \
                                                .filter(complete=True)

    for i in esd_qs:
        i.pullPayPalResult(False)   

    history = []

    expenditure_report = data["expenditure_report"]
    
    #paypal
    budget_list = profile.objects.filter(type=1)
    account_list = accounts.objects.filter(archived=False)

    if expenditure_report["budget"] != "":
        budget_list = budget_list.filter(id=expenditure_report["budget"])

    if expenditure_report["department"] != "":
        account_list = account_list.filter(department=expenditure_report["department"])

    for b in budget_list:        

        for a in account_list:
            session_list = experiment_session_days.objects.filter(experiment_session__budget=b.user) \
                                                          .filter(complete=True) \
                                                          .filter(account=a) \
                                                          .filter(date__gte=s_date) \
                                                          .filter(date__lte=e_date) \
                                                          .order_by('experiment_session__experiment__title', 'date')

            result={}
            result['id']=b.user.id
            result['total']=Decimal("0")
            result['total_international']=Decimal("0")
            result['total_unclaimed']=Decimal("0")
            result['sessions']=[]            

            for s in session_list:
                if s.ESDU_b.filter(confirmed=True).count() > 0:
                    session_total = Decimal("0")

                    if s.paypal_api:
                        realized_totals = s.get_paypal_realized_totals()
                        result['total'] += realized_totals['realized_fees']
                        result['total'] += realized_totals['realized_payouts']
                        result['total_international'] += realized_totals['realized_payouts_international']
                        result['total_unclaimed'] += realized_totals['unclaimed']

                        session_total = realized_totals['realized_fees'] \
                                       + realized_totals['realized_payouts'] \
                                       + realized_totals['unclaimed'] \
                                       + gross_up(realized_totals['realized_payouts_international']) 
                    else:
                        total = s.get_cash_payout_total()
                        
                        if total.get('show_up_fee', None):
                            result['total'] += total['show_up_fee']
                            result['total'] += total['earnings']
                            result['total_international'] += total['show_up_fee_international']
                            result['total_international'] += total['earnings_international']

                            session_total = total['show_up_fee'] + total['earnings'] + \
                                            gross_up(total['show_up_fee_international']) + \
                                            gross_up(total['earnings_international'])

                    result['sessions'].append({'id':s.id, 
                                               'title':s.experiment_session.experiment.title,
                                               'paypal_api': s.paypal_api,
                                               'session_total' : f'{session_total:0.2f}'})
            
            if result['total'] > 0 :
                result['name']=f'{b.user.last_name}, {b.user.first_name}'
                result['account_name']=a.name
                result['account_number']=a.number
                result['department']=a.department.name
                result['total'] = f'{result["total"]:0.2f}'
                result['total_international'] = f'{gross_up(result["total_international"]):0.2f}'
                result['total_unclaimed'] = f'{result["total_unclaimed"]:0.2f}'
                history.append(result)
    
    #no budget defined
    session_list = experiment_session_days.objects.filter(experiment_session__budget=None) \
                                                  .filter(complete=True) \
                                                  .filter(date__gte=s_date) \
                                                  .filter(date__lte=e_date) \
                                                  .order_by('experiment_session__experiment__title')  

    result={}
    result['id']=-1
    result['total']=Decimal("0")
    result['total_international']=Decimal("0")
    result['total_unclaimed']=Decimal("0")
    result['sessions']=[] 

    for s in session_list:
        if s.ESDU_b.filter(confirmed=True).count() > 0:                             
            session_total = Decimal("0")
            
            if s.paypal_api:
                realized_totals = s.get_paypal_realized_totals()
                result['total'] += realized_totals['realized_fees']
                result['total'] += realized_totals['realized_payouts']
                result['total_unclaimed'] += realized_totals['unclaimed']
                result['total_international'] += realized_totals['realized_payouts_international']

                session_total =  realized_totals['realized_fees'] \
                               + realized_totals['realized_payouts'] \
                               + realized_totals['unclaimed'] \
                               + gross_up(realized_totals['realized_payouts_international']) 
            else:
                total = s.get_cash_payout_total()
                
                if total.get('show_up_fee', None):
                    result['total'] += total['show_up_fee']
                    result['total'] += total['earnings']
                    result['total_international'] += total['show_up_fee_international']
                    result['total_international'] += total['earnings_international']

                    session_total = total['show_up_fee'] + total['earnings'] + \
                                    gross_up(total['show_up_fee_international']) + \
                                    gross_up(total['earnings_international'])

            result['sessions'].append({'id':s.id, 
                                       'title':s.experiment_session.experiment.title,
                                        'paypal_api': s.paypal_api,
                                        'session_total' : f'{session_total:0.2f}'})
            
    if result['total'] > 0 :
        result['name']='No Budget'
        result['account_name'] = ''
        result['account_number'] = ''
        result['department'] =  ''
        result['total'] = f'{result["total"]:0.2f}'
        result['total_unclaimed'] = f'{result["total_unclaimed"]:0.2f}'
        result['total_international'] = f'{gross_up(result["total_international"]):0.2f}'
        history.append(result)                  

    #create csv version of data

    output = io.StringIO()

    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    writer.writerow(["Budget","Account Name","Account Number","Department", "Session", "Payments"])

    for budget in history:

        for session in budget["sessions"]:

            writer.writerow([budget["name"], 
                             budget["account_name"], 
                             budget["account_number"],
                             budget["department"],
                             session["title"],
                             session["session_total"],
                             ])

    return JsonResponse({"history" : history, 
                         "history_csv" : output.getvalue(),
                         "errorMessage":error_message}, safe=False)




