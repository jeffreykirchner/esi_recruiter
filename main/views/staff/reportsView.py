from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
import logging
from main.forms import pettyCashForm
from main.models import departments,experiment_session_days,accounts,parameters
import csv
import pytz
from django.http import HttpResponse
from django.db.models import Avg, Count, Min, Sum, Q
from django.db.models import Case,Value,When

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

#generate the petty cash csv report
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

        p = parameters.objects.get(id=1)
        tz = pytz.timezone(p.subjectTimeZone)

        dpt = form.cleaned_data['department']
        s_date = form.cleaned_data['startDate'] 
        e_date = form.cleaned_data['endDate']  

        ESD = experiment_session_days.objects.annotate(totalEarnings = Sum(Case( When(experiment_session_day_users__attended = 1,
                                                                                 then = 'experiment_session_day_users__earnings'),
                                                                                 default = Value(0) )))\
                                             .annotate(totalBumps = Sum(Case(When(experiment_session_day_users__bumped = 1,
                                                                               then = 'experiment_session_day_users__show_up_fee'),
                                                                             When(experiment_session_day_users__attended = 1,
                                                                               then = 'experiment_session_day_users__show_up_fee'),
                                                                             default=Value(0)  )))\
                                             .filter(account__in = dpt.accounts_set.all(),
                                                     date__gte=s_date,
                                                     date__lte=e_date)\
                                             .filter(Q(totalEarnings__gt = 0) | 
                                                     Q(totalBumps__gt = 0))\
                                             .select_related('experiment_session__experiment','account')\
                                             .order_by('date')
        
        ESD_accounts_ids = experiment_session_days.objects.filter(account__in = dpt.accounts_set.all(),
                                                     date__gte=s_date,
                                                     date__lte=e_date)\
                                              .values_list('account_id',flat=True).distinct()                                            

        ESD_accounts = accounts.objects.filter(id__in=ESD_accounts_ids)
        logger.info(ESD_accounts)

        csv_response = HttpResponse(content_type='text/csv')
        csv_response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

        writer = csv.writer(csv_response)    

        #title
        writer.writerow(["Petty Cash Reconciliation Report - " + str(s_date.astimezone(tz).strftime("%-m/%#d/%Y")) + " to " + str(e_date.astimezone(tz).strftime("%-m/%#d/%Y")) + " for Department ESI"]) 
        writer.writerow([])

         
        #column header
        columnSums = [0]       
        columnHeader1 = ['Title','Date','Amount']
        for a in ESD_accounts.all():
            columnHeader1.append(a.number)
            columnSums.append(0)
        writer.writerow(columnHeader1)

        #session days
        for d in ESD:
            temp=[]
            totalPayout = "$" + f'{d.totalEarnings+d.totalBumps:.2f}'

            temp.append(d.experiment_session.experiment.title)
            temp.append(d.date.astimezone(tz).strftime("%-m/%#d/%Y"))
            temp.append(totalPayout)

            columnSums[0] +=  d.totalEarnings+d.totalBumps

            i = 1
            for a in ESD_accounts.all():
                if d.account == a:
                    temp.append(totalPayout)
                    columnSums[i] += d.totalEarnings+d.totalBumps
                else:
                    temp.append("-")
                
                i += 1

            writer.writerow(temp)        

        #totals
        totalsRow = ["Grand Totals",""]
        for i in columnSums:
            totalsRow.append("$" + f'{i:.2f}')

        writer.writerow([])
        writer.writerow(totalsRow)

        #petty cash
        writer.writerow([])
        writer.writerow([])
        writer.writerow([])
        writer.writerow(['Petty Cash Advanced','',"$" + f'{dpt.petty_cash:.2f}'])
        writer.writerow(['Amount in Cash Box','',"$" + f'{-1 * columnSums[0]:.2f}'])

        #signatures
        writer.writerow([])
        writer.writerow([])
        writer.writerow(["Turned into Cashier's"])
        writer.writerow([])
        writer.writerow(['O/S charge to'])
        writer.writerow([dpt.charge_account + "   $" + f'{columnSums[0] - dpt.petty_cash:.2f}'])
        writer.writerow([])
        writer.writerow([])
        writer.writerow(["Cashier                                     _____________________________________________"])
        writer.writerow([])
        writer.writerow([])
        writer.writerow(["Department Representative     _____________________________________________"])
                       
        return csv_response
    else:
        logger.info("invalid pretty form")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

    