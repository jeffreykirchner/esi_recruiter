import json
import logging
import calendar
import pytz

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import CharField,F,Value as V
from django.views import View
from django.utils.decorators import method_decorator
from django.views.generic.detail import SingleObjectMixin

from main.decorators import user_is_staff

from main.models import ExperimentSessionDays
from main.models import locations
from main.models import parameters
from main.models import HelpDocs

from main.globals import todays_date

class CalendarView(View):
    '''
    Calendar View
    '''

    template_name = "staff/calendar.html"

    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logger = logging.getLogger(__name__)

        try:
            helpText = HelpDocs.objects.annotate(rp = V(request.path,output_field=CharField()))\
                                        .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
            helpText = "No help doc was found."


        month = kwargs.get('month', None)
        year = kwargs.get('year', None)

        #build month list
        current_date = todays_date()

        month_list=[]

        current_date += relativedelta(months=12)

        while current_date.year >= 2008:
            month_list.append(get_month_jump_display_json(current_date))

            current_date -= relativedelta(months=1)

        logger = logging.getLogger(__name__) 
        logger.info(f"Get calendar: url month:{month}, url year:{year}")
            

        return render(request,
                      self.template_name,
                      {"helpText":helpText ,
                       "month_list":month_list,
                       "id":""})
    
    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__) 

        data = json.loads(request.body.decode('utf-8'))

        month = kwargs.get('month', None)
        year = kwargs.get('year', None)

        if data["action"] == "getMonth":
            return get_month(request, data, month, year)
        elif data["action"] == "changeMonth":
            return change_month(request, data)
        elif data["action"] == "jump_to_month":
            return jump_to_month(request, data)
           
        return JsonResponse({"response" :  "error"},safe=False)

def get_month_jump_display_json(date):
    '''
    return the json output for jumping to a new month
    date :  datetime
    '''
    return {"year" : date.year, "month" : date.month, "display" : date.strftime("%B, %Y")}

def get_month(request, data, month, year):
    '''
    get current month's data
    data: {}
    '''
    logger = logging.getLogger(__name__) 
    logger.info(f"Get month: {data}, url month:{month}, url year:{year}")

    p = parameters.objects.first()

    #today's month
    tz = pytz.timezone(p.subjectTimeZone)
    t = datetime.now(tz)

    if not month or not data["load_url_month"]:
        month = t.month
        year = t.year
    
    #month to show
    t_current = datetime.strptime(str(month) + " " + str(year), '%m %Y')

    return JsonResponse({"currentMonth" :  month,
                         "currentYear" : year,
                         "todayMonth": t.month,
                         "todayYear": t.year,
                         "todayDay": t.day,
                         "locations" : [l.json() for l in locations.objects.all()],
                         "currentMonthString" :  t_current.strftime("%B, %Y"),
                         "jump_to_month" : str(get_month_jump_display_json(t_current)),
                         "calendar": get_calendar_json(month, year)},safe=False)

def change_month(request, data):
    '''
    change month displayed, to next month or previous month
    data: {direction, currentMonth, currentYear}
    '''
    logger = logging.getLogger(__name__) 
    logger.info(f"Change month: {data}")

    direction = data["direction"]
    currentMonth = int(data["currentMonth"])
    currentYear = int(data["currentYear"])

    if direction == "current":
        p = parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)
        t = datetime.now(tz)
    elif direction == "previous":
        t = datetime.strptime(str(currentMonth) + " " + str(currentYear), '%m %Y')
        #logger.info(t)

        currentMonth-=1
        if currentMonth == 0:
            currentMonth = 12
            currentYear -= 1

        t = datetime.strptime(str(currentMonth) + " " + str(currentYear), '%m %Y')    
        #logger.info(t)
    elif direction == "next":
        t = datetime.strptime(str(currentMonth) + " " + str(currentYear), '%m %Y')
        #logger.info(t)

        currentMonth+=1
        if currentMonth == 13:
            currentMonth = 1
            currentYear += 1

        t = datetime.strptime(str(currentMonth) + " " + str(currentYear), '%m %Y')    
        #logger.info(t)

    #request.session['currentMonth'] = t
    
    logger.info(f"change month :{t.month}")

    return JsonResponse({"currentMonth" :  t.month,
                         "currentYear" : t.year,
                         "currentMonthString" :  t.strftime("%B, %Y"),
                         "jump_to_month" : str(get_month_jump_display_json(t)),
                         "calendar": get_calendar_json(t.month, t.year)},safe=False)

def jump_to_month(request, data):
    '''
    jump to a specfic month
    data: get_month_jump_display_json() format
    '''
    logger = logging.getLogger(__name__) 
    logger.info(f"Jump to month: {data}")

    new_month = json.loads(data["new_month"].replace("\'", "\""))

    t = datetime.strptime(str(new_month["month"]) + " " + str(new_month["year"]), '%m %Y')    

    return JsonResponse({"currentMonth" :  t.month,
                         "currentYear" : t.year,
                         "currentMonthString" :  t.strftime("%B, %Y"),
                         "jump_to_month" : str(get_month_jump_display_json(t)),
                         "calendar": get_calendar_json(t.month, t.year)},safe=False)


def get_calendar_json(month, year):
    '''
    get the calendar month in json format
    month : int
    year : int
    '''
    logger = logging.getLogger(__name__) 
    logger.info("Get Calendar JSON")

    #test code
    #month = 3
    #year = 2020

    p = parameters.objects.first()
    tz = pytz.timezone(p.subjectTimeZone)

    cal_full = []

    cal = calendar.Calendar(calendar.SUNDAY).monthdatescalendar(year, month)
    
    first_day = datetime.strptime(str(cal[0][0]) + " 00:00:00 -0000","%Y-%m-%d %H:%M:%S %z")
    last_day = datetime.strptime(str(cal[-1][-1]) + " 23:59:59 -0000","%Y-%m-%d %H:%M:%S %z")


    #logger.info(first_day)
    #logger.info(last_day)

    s_list = list(ExperimentSessionDays.objects.filter(date__gte = first_day,
                                                         date__lte = last_day)\
                                                 .order_by("date")\
                                                 .select_related('experiment_session','experiment_session__experiment','location','experiment_session__experiment'))

    #logger.info(s_list)

    for w in cal:
        new_week=[]

        for d in w:           
  
            s_list_local=[]

            for s in s_list:
                #logger.info(s.date.day)
                s_date_local = s.date.astimezone(tz)
                if s_date_local.day == d.day and s_date_local.month == d.month and s_date_local.year == d.year:
                    s_list_local.append({"id" : s.id, 
                                         "session_id" : s.experiment_session.id,
                                         "experiment_id" : s.experiment_session.experiment.id,                                        
                                         "name" : s.experiment_session.experiment.title,
                                         "manager" : s.experiment_session.experiment.experiment_manager,
                                         "canceled" : s.experiment_session.canceled,
                                         "location" : s.location.json(),
                                         "enable_time" : s.enable_time,
                                         "startTime" : s.getStartTimeString(),
                                         "endTime" : s.getEndTimeString()})

            #add extra spacers
            for i in range(len(s_list_local),4):
                s_list_local.append({"id" : i,   
                                    "name" : "",
                                    "manager" : "",
                                    "canceled" : False,
                                    "location" : {"id":0,"name":""},
                                    "startTime" : "",
                                    "endTime" : ""})


            new_week.append({"day" : d.day,
                             "month" : d.month,
                             "year" : d.year,
                             "weekday" : d.strftime('%a'),
                             "dayString" :  d.strftime("%B %-d, %Y"),
                             "sessions" : s_list_local
                             })
            #logger.info(d)
            

        cal_full.append(new_week)

    #logger.info(cal.monthdatescalendar(year, month))

    return cal_full