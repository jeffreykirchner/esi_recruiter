import json
import logging
import csv
import pytz

from decimal import Decimal
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.db.models import Avg, Count, Min, Sum, Q, F, CharField, Value as V
from django.db.models import Case, Value, When, DecimalField
from django.views import View
from django.utils.decorators import method_decorator

from main.decorators import user_is_staff

from main.forms import pettyCashForm
from main.forms import studentReportForm
from main.models import Departments
from main.models import experiment_session_days
from main.models import Accounts
from main.models import parameters 
from main.models import ExperimentSessionDayUsers
from main.models import help_docs

class ReportsView(View):
    '''
    reports view
    '''

    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logger = logging.getLogger(__name__)

        p = parameters.objects.first()

        try:
            helpText = help_docs.objects.annotate(rp = V(request.path,output_field=CharField()))\
                                    .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
            helpText = "No help doc was found."


        param = parameters.objects.first()
        tmz = pytz.timezone(param.subjectTimeZone)
        d_today = datetime.now(tmz)

        #start of fiscal year
        d_fisical_start = d_today
        d_fisical_start = d_fisical_start.replace(month=6, day=1)

        if d_today.month<6:
            d_fisical_start = d_fisical_start.replace(year=d_fisical_start.year-1)

        return render(request,'staff/reports.html',{"pettyCashForm" : pettyCashForm() ,
                                                    "studentReportForm" : studentReportForm(),
                                                    "maxAnnualEarnings":p.maxAnnualEarnings,
                                                    "d_today" : d_today.date().strftime("%Y-%m-%d"),
                                                    "d_fisical_start" : d_fisical_start.date().strftime("%Y-%m-%d"),
                                                    "helpText":helpText})
    
    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__)

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getPettyCash":
            return pettyCash(data)
        elif data["action"] == "getStudentReport":
            return studentReport(data)
           
        return JsonResponse({"response" :  "fail"},safe=False)

#generate the student csv report
def studentReport(data):
    logger = logging.getLogger(__name__)
    logger.info(f"Get Student Report CSV: {data}")

    form_data_dict = data["formData"]

    # for field in data["formData"]:            
    #     form_data_dict[field["name"]] = field["value"]
    
    form = studentReportForm(form_data_dict)

    if form.is_valid():
        #print("valid form")   

        p = parameters.objects.first()
        tz = pytz.timezone(p.subjectTimeZone)

        studentReport_nra = form.cleaned_data['studentReport_nra'] 
        studentReport_gt600 = form.cleaned_data['studentReport_gt600'] 
        studentReport_studentWorkers = form.cleaned_data['studentReport_studentWorkers']  
        studentReport_department_or_account = form.cleaned_data['studentReport_department_or_account']  
        studentReport_include_archived = form.cleaned_data['studentReport_include_archived']
        studentReport_outside_funding = form.cleaned_data['studentReport_outside_funding']

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
        ESDU = ExperimentSessionDayUsers.objects.filter(experiment_session_day__date__gte=s_date,
                                                           experiment_session_day__date__lte=e_date,)\
                                                   .filter((Q(attended = 1) & (Q(earnings__gt = 0) | Q(show_up_fee__gt = 0))) | 
                                                           (Q(bumped = 1) & Q(show_up_fee__gt = 0)))\
                                                   .order_by('user__last_name', 'user__first_name')\
                                                   .select_related('experiment_session_day',
                                                                   'user',
                                                                   'user__profile',
                                                                   'experiment_session_day__account')
        acnts = Accounts.objects.all()
        depts = Departments.objects.all().prefetch_related('accounts_set')

        #outside funding
        if studentReport_outside_funding == "1":
            ESDU = ESDU.filter(experiment_session_day__account__outside_funding=True)
            acnts = acnts.filter(outside_funding=True)
        elif studentReport_outside_funding == "0":
            ESDU = ESDU.filter(experiment_session_day__account__outside_funding=False)
            acnts = acnts.filter(outside_funding=False)

        if studentReport_include_archived == "0":
            acnts = acnts.filter(archived=False)
            ESDU = ESDU.filter(experiment_session_day__account__archived=False)

        #filter for international_student
        if studentReport_nra == "1":
            ESDU = ESDU.filter(user__profile__international_student = True)

        #filter for student workers
        if studentReport_studentWorkers == "1":
            ESDU = ESDU.filter(user__profile__studentWorker = True)

        #list of unique subjects in range
        ESDU_ids = ESDU.values_list('user__id',flat=True).distinct()

        # logger.info(ESDU)
        # logger.info(ESDU_ids)

        headerText = ['ID','Name','Email','International','Student Worker','Payments','Total Earnings in Range']

        if studentReport_department_or_account == "Department":
            for i in depts:
                headerText.append(i.name)
        else:
            for i in acnts:
                headerText.append(i.number)

        writer.writerow(headerText)

        for i in ESDU_ids:

            #total by department
            if studentReport_department_or_account == "Department":
                depts_total={}
                for j in depts:
                    depts_total[j.id] = 0
            else:
                acnts_total={}
                for j in acnts:
                    acnts_total[j.id] = 0

            tempL = ESDU.filter(user__id = i)

            #running total
            tempTotal = 0

            u = ESDU.filter(user__id = i).first().user

            #list of experiments
            e_list = ""
            for j in tempL:
                temp_e = j.get_total_payout()
                                
                #running total
                tempTotal += temp_e

                if studentReport_department_or_account == "Department":
                    depts_total[j.experiment_session_day.account.department.id] += temp_e
                else:
                    acnts_total[j.experiment_session_day.account.id] += temp_e

                if e_list != "":
                    e_list +=", "

                e_list +=  f'(${temp_e:.2f}) {j.experiment_session_day.date.astimezone(tz).strftime("%-m/%#d/%Y")}' 
            
            output_text=[u.profile.studentID,
                         u.last_name + ', ' + u.first_name,
                         u.email,
                         u.profile.international_student,
                         u.profile.studentWorker,
                         e_list,                            
                         f'${tempTotal:.2f}']
            
            if studentReport_department_or_account == "Department":
                for j in depts_total:
                    output_text.append(f'${depts_total[j]:2f}')
            else:
                 for j in acnts_total:
                    output_text.append(f'${acnts_total[j]:2f}')

            if (studentReport_gt600 == "1" and tempTotal >= p.maxAnnualEarnings) or studentReport_gt600 != "1":
                writer.writerow(output_text)        
                       
        return csv_response
    else:
        logger.info("invalid student report form")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

#generate the petty cash csv report
def pettyCash(data):
    logger = logging.getLogger(__name__)
    logger.info(f"Get Petty Cash CSV: {data}")

    form_data_dict = data["formData"]

    # for field in data["formData"]:            
    #     form_data_dict[field["name"]] = field["value"]
    
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

        ESD = experiment_session_days.objects.annotate(totalEarnings=Sum(Case(When(ESDU_b__attended = 1,
                                                                                 then = 'ESDU_b__earnings'),
                                                                                 default = Decimal("0")),
                                                                        output_field=DecimalField()))\
                                             .annotate(totalBumps=Sum(Case(When(ESDU_b__bumped = 1,
                                                                               then = 'ESDU_b__show_up_fee'),
                                                                             When(ESDU_b__attended = 1,
                                                                               then = 'ESDU_b__show_up_fee'),
                                                                             default=Decimal("0")),
                                                                        output_field=DecimalField()))\
                                             .filter(account__in = dpt.accounts_set.filter(outside_funding=False),
                                                     date__gte=s_date,
                                                     date__lte=e_date)\
                                             .filter(Q(totalEarnings__gt = 0) | 
                                                     Q(totalBumps__gt = 0))\
                                             .select_related('experiment_session__experiment','account')\
                                             .order_by('date')
        
        ESD_accounts_ids = experiment_session_days.objects.filter(account__in = dpt.accounts_set.filter(outside_funding=False),
                                                     date__gte=s_date,
                                                     date__lte=e_date)\
                                              .values_list('account_id',flat=True).distinct()                                            

        ESD_accounts = Accounts.objects.filter(id__in=ESD_accounts_ids)\
                                       .filter(outside_funding=False)

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
        totalsRow = ["Grand Totals","",""]
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

    