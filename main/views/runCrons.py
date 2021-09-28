import logging
import json


from django.http import JsonResponse

from main.cron import checkForReminderEmails
from main.cron import check_send_daily_report_email

def runCronsView(request):
    
    if request.method == 'POST':       

        #data = json.loads(request.body.decode('utf-8'))

        return JsonResponse({"" : ""
                                 },safe=False,
                                )      
                   
    else:     
       logger = logging.getLogger(__name__) 
       logger.info("Run Crons View")
       
       #reminder emails
       cj = checkForReminderEmails()

       r = cj.do()
       logger.info(r)
       
       status_reminder_email = f'Sent {r}'

       #daily report email
       r = check_send_daily_report_email()
       logger.info(r)

       status_report_email = f'{r}'

       return JsonResponse({"status reminder email" : status_reminder_email,
                            "status report email" :   status_report_email,  
                            },safe=False,)  

    

    