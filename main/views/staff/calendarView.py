from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
import logging
from datetime import datetime,timedelta
import calendar
from main.models import experiment_session_days,locations,parameters,help_docs
from django.utils.timezone import make_aware
import pytz
from django.utils import timezone
from django.db.models import CharField,Q,F,Value as V

@login_required
@user_is_staff
def calendarView(request):
    logger = logging.getLogger(__name__) 
    
    # logger.info("some info")

    if request.method == 'POST':       

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getMonth":
            return getMonth(request,data)
        elif data["action"] == "changeMonth":
            return changeMonth(request,data)
           
            return JsonResponse({"response" :  "some json"},safe=False)       
    else:   

        try:
            helpText = help_docs.objects.annotate(rp = V(request.path,output_field=CharField()))\
                                    .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
            helpText = "No help doc was found."

        return render(request,'staff/calendar.html',{"helpText":helpText ,"id":""})      

#get current month
def getMonth(request,data):
    logger = logging.getLogger(__name__) 
    logger.info("Get month")
    logger.info(data)

    p = parameters.objects.first()
    tz = pytz.timezone(p.subjectTimeZone)
    t = datetime.now(tz)


    return JsonResponse({"currentMonth" :  t.month,
                         "currentYear" : t.year,
                         "currentDay": t.day,
                         "locations" : [l.json() for l in locations.objects.all()],
                         "currentMonthString" :  t.strftime("%B, %Y"),
                         "calendar": getCalendarJson(t.month,t.year)},safe=False)

#change the current month viewed
def changeMonth(request,data):
    logger = logging.getLogger(__name__) 
    logger.info("Get month")
    logger.info(data)

    direction = data["direction"]
    currentMonth =int(data["currentMonth"])
    currentYear = int(data["currentYear"])

    if direction == "current":
        p = parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)
        t = datetime.now(tz)
    elif direction == "previous":
        t = datetime.strptime(str(currentMonth) + " " + str(currentYear), '%m %Y')
        logger.info(t)

        currentMonth-=1
        if currentMonth == 0:
            currentMonth = 12
            currentYear -= 1

        t = datetime.strptime(str(currentMonth) + " " + str(currentYear), '%m %Y')    
        logger.info(t)
    elif direction == "next":
        t = datetime.strptime(str(currentMonth) + " " + str(currentYear), '%m %Y')
        logger.info(t)

        currentMonth+=1
        if currentMonth == 13:
            currentMonth = 1
            currentYear += 1

        t = datetime.strptime(str(currentMonth) + " " + str(currentYear), '%m %Y')    
        logger.info(t)

    #request.session['currentMonth'] = t
    
    logger.info(t.month)

    return JsonResponse({"currentMonth" :  t.month,
                         "currentYear" : t.year,
                         "currentMonthString" :  t.strftime("%B, %Y"),
                         "calendar": getCalendarJson(t.month,t.year)},safe=False)

#get calendar arrays
def getCalendarJson(month,year):
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

    s_list = list(experiment_session_days.objects.filter(date__gte = first_day,
                                                         date__lte = last_day)\
                                                 .order_by("date")\
                                                 .select_related('experiment_session','experiment_session__experiment','location'))

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
                             "dayString" :  d.strftime("%B %-d, %Y"),
                             "sessions" : s_list_local
                             })
            #logger.info(d)
            

        cal_full.append(new_week)

    #logger.info(cal.monthdatescalendar(year, month))

    return cal_full