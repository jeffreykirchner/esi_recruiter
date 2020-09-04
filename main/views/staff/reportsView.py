from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
import logging
from main.forms import pettyCashForm
from main.models import departments,experiment_session_days,accounts
import csv
from django.http import HttpResponse
from django.db.models import Avg, Count, Min, Sum

@login_required
@user_is_staff
def reportsView(request):
    logger = logging.getLogger(__name__) 
    

    if request.method == 'POST':       

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getPettyCash":
            return pettyCash(data)
        elif data["action"] == "action2":
            pass
           
        return JsonResponse({"response" :  "fail"},safe=False)       
    else:      

        return render(request,'staff/reports.html',{"pettyCashForm":pettyCashForm() ,
                                                    "id":""})      

def pettyCash(data):
    logger = logging.getLogger(__name__)
    logger.info("Get Petty Cash CSV")
    logger.info(data)

    form_data_dict = {}

    for field in data["formData"]:            
        form_data_dict[field["name"]] = field["value"]
    
    form = pettyCashForm(form_data_dict)

    if form.is_valid():
        #print("valid form")   

        d = form.cleaned_data['department']
        s_date = form.cleaned_data['startDate'] 
        e_date = form.cleaned_data['endDate']  

        ESD = experiment_session_days.objects.filter(account__in = d.accounts_set.all(),
                                                     date__gte=s_date,
                                                     date__lte=e_date)\
                                              .annotate(totalPayout = Sum('experiment_session_day_users__earnings'))\
                                              .select_related('experiment_session__experiment','account')\
                                              .order_by('date')
        
        ESD_accounts_ids = experiment_session_days.objects.filter(account__in = d.accounts_set.all(),
                                                     date__gte=s_date,
                                                     date__lte=e_date)\
                                              .values_list('account_id',flat=True).distinct()

        ESD_accounts = accounts.objects.filter(id__in=ESD_accounts_ids)
        logger.info(ESD_accounts)

        csv_response = HttpResponse(content_type='text/csv')
        csv_response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

        writer = csv.writer(csv_response)    

        #title
        writer.writerow(["Petty Cash Reconciliation Report - " + str(s_date) + " to " + str(e_date) + " for Department ESI"]) 
        writer.writerow([])

        #column header
        columnHeader1 = ['Title,Date,Amount']
        for a in ESD_accounts.all():
            columnHeader1.append(a.number)
        writer.writerow(columnHeader1)

        #session days
        for d in ESD:
            temp=[]

            temp.append(d.experiment_session.experiment.title)
            temp.append(str(d.date))
            temp.append(d.totalPayout)

            writer.writerow(temp)        


                       
        return csv_response
    else:
        logger.info("invalid pretty form")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

    