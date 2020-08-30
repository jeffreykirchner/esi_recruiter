from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
import logging
from datetime import datetime,timedelta

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
                         "currentYear" : str(t.year)},safe=False)

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
                         "currentYear" : t.year},safe=False)