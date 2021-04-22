from decimal import Decimal
from datetime import datetime, timedelta, timezone

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
import logging
from main.forms import pettyCashForm, studentReportForm
from main.models import departments,experiment_session_days,accounts,parameters,experiment_session_day_users,help_docs
import csv
import pytz
from django.utils.timezone import make_aware
from django.http import HttpResponse
from django.db.models import Avg, Count, Min, Sum, Q,F,CharField,Value as V
from django.db.models import Case, Value, When, DecimalField


@login_required
@user_is_staff
def reportsView(request):
    logger = logging.getLogger(__name__)     

    if request.method == 'POST':       

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getPettyCash":
            return pettyCash(data)
        elif data["action"] == "getStudentReport":
            return studentReport(data)
           
        return JsonResponse({"response" :  "fail"},safe=False)       
    else:      
        p = parameters.objects.first()

        try:
            helpText = help_docs.objects.annotate(rp = V(request.path,output_field=CharField()))\
                                    .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
            helpText = "No help doc was found."

        return render(request,'staff/reports.html',{"pettyCashForm" : pettyCashForm() ,
                                                    "studentReportForm" : studentReportForm(),
                                                    "maxAnnualEarnings":p.maxAnnualEarnings,
                                                    "helpText":helpText})      

#generate the student csv report
def studentReport(data):
    logger = logging.getLogger(__name__)
    logger.info("Get Student Report CSV")
    logger.info(data)

    form_data_dict = {}

    for field in data["formData"]:            
        form_data_dict[field["name"]] = field["value"]
    
    form = studentReportForm(form_data_dict)

    if form.is_valid():
        #print("valid form")   

        p = parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)

        studentReport_nra = form.cleaned_data['studentReport_nra'] 
        studentReport_gt600 = form.cleaned_data['studentReport_gt600'] 
        studentReport_studentWorkers = form.cleaned_data['studentReport_studentWorkers']  

        logger.info(studentReport_studentWorkers)
        
        #non tz aware dates
        s_date_start = form.cleaned_data['studentReport_startDate'] 
        e_date_start = form.cleaned_data['studentReport_endDate']

        #create a new tz aware date time
        s_date = datetime.now(tz)
        e_date = datetime.now(tz)

        #replace with non aware info
        s_date = s_date.replace(day=s_date_start.day,month=s_date_start.month, year=s_date_start.year)
        e_date = e_date.replace(day=e_date_start.day,month=e_date_start.month, year=e_date_start.year)

        s_date = s_date.replace(hour=0,minute=0, second=0)
        e_date = e_date.replace(hour=23,minute=59, second=59)

        logger.info(s_date)
        logger.info(e_date)

        csv_response = HttpResponse(content_type='text/csv')
        csv_response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

        writer = csv.writer(csv_response)

        #session day list
        ESDU = experiment_session_day_users.objects.filter(experiment_session_day__date__gte=s_date,
                                                           experiment_session_day__date__lte=e_date,)\
                                                   .filter((Q(attended = 1) & (Q(earnings__gt = 0) | Q(show_up_fee__gt = 0))) | 
                                                           (Q(bumped = 1) & Q(show_up_fee__gt = 0)))\
                                                   .order_by('user__last_name')\
                                                   .select_related('experiment_session_day','user','user__profile','experiment_session_day__account')

        #filter for nonresident aliens
        if studentReport_nra == "1":
            ESDU = ESDU.filter(user__profile__nonresidentAlien = True)

        #filter for nonresident aliens
        if studentReport_studentWorkers == "1":
            ESDU = ESDU.filter(user__profile__studentWorker = True)

        #list of unique subjects in range
        ESDU_ids = ESDU.values_list('user__id',flat=True).distinct()

        #list of accounts
        depts = departments.objects.all().prefetch_related('accounts_set') 

        logger.info(ESDU)
        logger.info(ESDU_ids)

        headerText = ['ID','Name','Email','Nonresident Alien','Student Worker','Payments','Total Earnings in Range']
        for i in depts:
            headerText.append(i.name)

        writer.writerow(headerText)

        for i in ESDU_ids:

            #total by department
            depts_total=[]
            for j in depts:
                depts_total.append(0)

            tempL = ESDU.filter(user__id = i)

            #running total
            tempTotal = 0

            u = ESDU.filter(user__id = i).first().user

            #list of experiments
            e_list = ""
            for j in tempL:
                temp_e=j.get_total_payout()
                # if(j.attended):
                #     temp_e = j.earnings + j.show_up_fee
                # elif(j.bumped):
                #     temp_e = j.show_up_fee
                
                #running total
                tempTotal+=temp_e

                #department total
                c=0
                for k in depts:
                    if j.experiment_session_day.account in k.accounts_set.all():
                        depts_total[c] += temp_e
                        break
                    c+=1

                if e_list != "":
                    e_list +=", "

                e_list +=  "($" + str(f'{temp_e:.2f}') + ") " +\
                           str(j.experiment_session_day.date.astimezone(tz).strftime("%-m/%#d/%Y")) 
            
            output_text=[u.profile.studentID,
                             u.last_name + ', ' + u.first_name,
                             u.email,
                             u.profile.nonresidentAlien,
                             u.profile.studentWorker,
                             e_list,                            
                            "$" + str(f'{tempTotal:.2f}')]
            
            for j in depts_total:
                output_text.append(j)

            if (studentReport_gt600 == "1" and tempTotal >= p.maxAnnualEarnings) or studentReport_gt600 != "1":
                writer.writerow(output_text)        
                       
        return csv_response
    else:
        logger.info("invalid student report form")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

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

        p = parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)

        dpt = form.cleaned_data['department']

        #non tz aware date
        s_date_start =  form.cleaned_data['startDate']
        e_date_start = form.cleaned_data['endDate'] 

        #create a new tz aware date time
        s_date = datetime.now(tz)
        e_date = datetime.now(tz)

        #replace with non aware info
        s_date = s_date.replace(day=s_date_start.day,month=s_date_start.month, year=s_date_start.year)
        e_date = e_date.replace(day=e_date_start.day,month=e_date_start.month, year=e_date_start.year)

        s_date = s_date.replace(hour=0,minute=0, second=0)
        e_date = e_date.replace(hour=23,minute=59, second=59)  

        logger.info(s_date)
        logger.info(e_date)      

        csv_response = HttpResponse(content_type='text/csv')
        csv_response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

        writer = csv.writer(csv_response)   

        ESD = experiment_session_days.objects.annotate(totalEarnings=Sum(Case(When(experiment_session_day_users__attended = 1,
                                                                                 then = 'experiment_session_day_users__earnings'),
                                                                                 default = Decimal("0")),
                                                                        output_field=DecimalField()))\
                                             .annotate(totalBumps=Sum(Case(When(experiment_session_day_users__bumped = 1,
                                                                               then = 'experiment_session_day_users__show_up_fee'),
                                                                             When(experiment_session_day_users__attended = 1,
                                                                               then = 'experiment_session_day_users__show_up_fee'),
                                                                             default=Decimal("0")),
                                                                        output_field=DecimalField()))\
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

        #title
        writer.writerow(["Petty Cash Reconciliation Report - " + str(s_date.astimezone(tz).strftime("%-m/%#d/%Y")) + " to " + str(e_date.astimezone(tz).strftime("%-m/%#d/%Y")) + " for Department ESI"]) 
        writer.writerow([])

         
        #column header
        columnSums = [0]       
        columnHeader1 = ['Title','Date','Time','Amount']
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
            temp.append(d.date.astimezone(tz).strftime("%#I:%M %p"))
            temp.append(totalPayout)

            columnSums[0] +=  d.totalEarnings + d.totalBumps

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
        logger.info("invalid petty cash form")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

    