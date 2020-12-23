from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.http import HttpResponse
import logging
from django.utils.safestring import mark_safe
from main.forms import traitReportForm
import csv

from main.models import Traits,profile_trait,profile

@login_required
@user_is_staff
def traitsView(request):
    logger = logging.getLogger(__name__) 
    
    # logger.info("some info")

    if request.method == 'POST':      

        u = request.user

        f=""
        
        try:
            f = request.FILES['file']
        except Exception  as e: 
            logger.info(f'traitsView no file upload: {e}')
            f = -1

        #check for file upload
        if f != -1:
            return takeCSVUpload(f,u)
        else:
            data = json.loads(request.body.decode('utf-8'))
            

            if data["action"] == "getReport":
                return getReport(data,u)
            elif data["action"] == "action2":
                pass
           
        return JsonResponse({"response" :  "fail"},safe=False)     

    else:      

        return render(request,'staff/traits.html',{"traitReportForm":traitReportForm()}) 

#get CSV file users with specified traits
def getReport(data,u):

    logger = logging.getLogger(__name__)
    logger.info("Get Trait Report CSV")
    logger.info(data)

    form_data_dict = {}
    traitsList=[]

    for field in data["formData"]:
        if field["name"] == "traits":
            traitsList.append(field["value"])
        else:
            form_data_dict[field["name"]] = field["value"]
    
    form_data_dict["traits"] = traitsList

    logger.info(form_data_dict)
    
    form = traitReportForm(form_data_dict)

    if form.is_valid():

        active_only = data["active_only"]

        traits_list = form.cleaned_data['traits']

        csv_response = HttpResponse(content_type='text/csv')
        csv_response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

        writer = csv.writer(csv_response)

        headerText = ['ID','Name','Email']

        for i in traits_list:
            headerText.append(i)

        writer.writerow(headerText)

        return csv_response
    else:
        logger.info("invalid trait report form")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

#take CSV file upload and store traits from it
def takeCSVUpload(f,u):
    logger = logging.getLogger(__name__) 
    logger.info("Take trait CSV upload")

    status = "success"
    message = ""

    logger.info(f"File to be uploaded {f}")

    #format incoming data
    v=""

    for chunk in f.chunks():
        v+=str(chunk.decode("utf-8"))            
    
    v=v.splitlines()

    for i in range(len(v)):
        v[i] = v[i].split(',')

    logger.info(v)

    #check that data is in correct format
    if v[0][0] !="num" or v[0][1] !="chapmanid" or v[0][2] != "fullname":
        status = "fail"
        message = "Invalid Format: No num, chapmaid or fullname column."

    #create any new traits that do not exist
    if status!="fail":
        for i in v[0]:                
            if i != "num" and i != "chapmanid" and i != "fullname":
                t = Traits.objects.filter(name = i).first()

                if not t:
                    t_new = Traits()
                    t_new.name = i
                    t_new.save()

                    message += f"New trait created: {i}<br>"
    
    #store traits
    if status != "fail":
        for i in range(1,len(v)):

            r = v[i]

            p = profile.objects.filter(studentID__icontains = int(r[1]))

            if len(p) == 1:
                p = p.first()
                # try:
                for j in range(3,len(r)):
                    #find trait and profile 
                    t = Traits.objects.filter(name = v[0][j]).first()
                    pt = profile_trait.objects.filter(my_profile = p,trait=t).first()

                    if pt:
                        #profile trait exists, update it 
                        pt.value = r[j]
                        pt.save()
                    else:
                        #profile trait does not exist, create a new one
                        pt = profile_trait()
                        pt.my_profile = p
                        pt.trait = t
                        pt.value = r[j]
                        pt.save()
                    
                message += f"Traits loaded for: <a href='/userInfo/{p.user.id}/'>{r[2]}</a><br>"

                # except Exception  as e: 
                #     status = "fail"
                #     message += f"Failed to load trait for:  {e}<br>"
            else:
                status = "fail"
                message += f"Subject not found: {r[2]}<br>"
    
    
    logger.info(f'Trait CSV upload result: {status} {message}')
    return JsonResponse({"response" : status,"message":message},safe=False)
