from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
import logging
from datetime import datetime,timedelta
import calendar
from main.models import experiment_session_days
from django.utils.timezone import make_aware
import pytz

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
        return render(request,'staff/calendar.html',{"u":"" ,"id":""})      

def getMonth(request,data):
    logger = logging.getLogger(__name__) 
    logger.info("Get month")
    logger.info(data)

    t = datetime.today()     

    return JsonResponse({"currentMonth" :  str(t.month),
                         "currentYear" : str(t.year),
                         "calendar": getCalendarJson(t.month,t.year)},safe=False)

def changeMonth(request,data):
    logger = logging.getLogger(__name__) 
    logger.info("Get month")
    logger.info(data)

    direction = data["direction"]
    currentMonth =int(data["currentMonth"])
    currentYear = int(data["currentYear"])

    if direction == "current":
        t = datetime.today()
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
                         "calendar": getCalendarJson(t.month,t.year)},safe=False)

def getCalendarJson(month,year):
    logger = logging.getLogger(__name__) 
    logger.info("Get Calendar JSON")

    #test code
    month = 3
    year = 2020

    cal_full = []

    cal = calendar.Calendar(calendar.SUNDAY).monthdatescalendar(year, month)
    
    first_day = datetime.strptime(str(cal[0][0]) + " 00:00:00 -0000","%Y-%m-%d %H:%M:%S %z")
    last_day = datetime.strptime(str(cal[-1][-1]) + " 23:59:59 -0000","%Y-%m-%d %H:%M:%S %z")


    logger.info(first_day)
    logger.info(last_day)

    s_list = list(experiment_session_days.objects.filter(date__gte = first_day,
                                                         date__lte = last_day)\
                                                 .order_by("location","date"))

    logger.info(s_list)

    for w in cal:
        new_week=[]

        for d in w:           
  
            s_list_local=[]

            for s in s_list:
                #logger.info(s.date.day)
                if s.date.day == d.day and s.date.month == d.month:
                    s_list_local.append({"id" : s.id,
                                         "name" : s.experiment_session.experiment.title,
                                         "room" : s.location.name,
                                         "startTime" : s.getStartTimeString(),
                                         "endTime" : s.getEndTimeString()})

            new_week.append({"day" : d.day,
                             "sessions" : s_list_local})
            #logger.info(d)
            

        cal_full.append(new_week)

    #logger.info(cal.monthdatescalendar(year, month))

    return cal_full