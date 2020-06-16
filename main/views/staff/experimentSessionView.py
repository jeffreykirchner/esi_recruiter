from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from main.decorators import user_is_staff
from main.models import experiment_session_days, \
                        experiment_session_day_users, \
                        experiment_sessions, \
                        accounts, \
                        schools, \
                        institutions, \
                        experience_levels, \
                        genders
from main.forms import experimentSessionForm1,experimentSessionForm2
from django.http import JsonResponse
from django.core import serializers
from django.forms.models import model_to_dict
import json
from django.db.models import prefetch_related_objects
from django.conf import settings

#induvidual experiment view
@login_required
@user_is_staff
def experimentSessionView(request,id):
       
    status = ""     
  

    if request.method == 'POST':
        
        data = json.loads(request.body.decode('utf-8'))         

        try:
            es = experiment_sessions.objects.get(id=id)  
        except es.DoesNotExist:
            raise Http404('Experiment Not Found')               

        if data["status"] == "get":

            # i_json = []
            #e_json = e.json()

            # for i in institutions.objects.all():
            #     i_json.append(i.json())
            
            return JsonResponse({"session" :  es.json()}, safe=False)
        elif data["status"] == "update1":

            form_data_dict = {} 

            genderList=[]
            subjectTypeList=[]
            institutionsExcludeList=[]
            institutionsIncludeList=[]
            experimentsExcludeList=[]
            experimentsIncludeList=[]

            for field in data["formData"]:            
                if field["name"] == "gender":                 
                    genderList.append(field["value"])
                elif field["name"] == "subject_type":                 
                    subjectTypeList.append(field["value"])
                elif field["name"] == "institutions_exclude":                 
                    institutionsExcludeList.append(field["value"])
                elif field["name"] == "institutions_include":                 
                    institutionsIncludeList.append(field["value"])
                elif field["name"] == "experiments_exclude":                 
                    experimentsExcludeList.append(field["value"])
                elif field["name"] == "experiments_include":                 
                    experimentsIncludeList.append(field["value"])
                else:
                    form_data_dict[field["name"]] = field["value"]

            form_data_dict["gender"]=genderList
            form_data_dict["subject_type"]=subjectTypeList
            form_data_dict["institutions_exclude"]=institutionsExcludeList
            form_data_dict["institutions_include"]=institutionsIncludeList
            form_data_dict["experiments_exclude"]=experimentsExcludeList
            form_data_dict["experiments_include"]=experimentsIncludeList                       

            #print(form_data_dict)
            form = experimentSessionForm1(form_data_dict,instance=es)

            if form.is_valid():
                #print("valid form")                
                e=form.save()               
                return JsonResponse({"session" : e.json(),"status":"success"}, safe=False)
            else:
                print("invalid form1")
                return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)         
        elif data["status"] ==  "addSessionDay":
            esd=experiment_session_days()
            esd.setup(es)
            esd.save()

            es.save()
            es = experiment_sessions.objects.get(id=id)

            return JsonResponse({"status":"success","sessionDays":es.json()}, safe=False)
        elif data["status"] ==  "removeSessionDay":
            es.experiment_session_days_set.get(id = data["id"]).delete()
            es.save()

            return JsonResponse({"status":"success","sessionDays":es.json()}, safe=False)
        elif data["status"] ==  "updateSessionDay":
            esd = experiment_session_days.objects.get(id= data["id"])            

            form_data_dict = {}            

            for field in data["formData"]:           
                form_data_dict[field["name"]] = field["value"]

            form = experimentSessionForm2(form_data_dict,instance=esd)

            # print(form_data_dict)

            if form.is_valid():
                esd.save()
                es.save()
                es = experiment_sessions.objects.get(id=id)

                return JsonResponse({"sessionDays" :es.json(),"status":"success"}, safe=False)
            else:
                print("invalid form2")
                return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)
        elif data["status"] ==  "removeSubject":
            esd=experiment_session_days.objects.get(id= data["id"])
            esdu=esd.experiment_session_day_users.objects.get(id=data["uid"])

        # elif data["status"] == "update2":   
        #     form_data_dict = {} 

        #     genderList=[]
        #     subjectTypeList=[]
        #     institutionsExcludeList=[]
        #     institutionsIncludeList=[]
        #     experimentsExcludeList=[]
        #     experimentsIncludeList=[]

        #     for field in data["formData"]:            
        #         if field["name"] == "gender_default":                 
        #             genderList.append(field["value"])
        #         elif field["name"] == "subject_type_default":                 
        #             subjectTypeList.append(field["value"])
        #         elif field["name"] == "institutions_exclude_default":                 
        #             institutionsExcludeList.append(field["value"])
        #         elif field["name"] == "institutions_include_default":                 
        #             institutionsIncludeList.append(field["value"])
        #         elif field["name"] == "experiments_exclude_default":                 
        #             experimentsExcludeList.append(field["value"])
        #         elif field["name"] == "experiments_include_default":                 
        #             experimentsIncludeList.append(field["value"])
        #         else:
        #             form_data_dict[field["name"]] = field["value"]

        #     form_data_dict["gender_default"]=genderList
        #     form_data_dict["subject_type_default"]=subjectTypeList
        #     form_data_dict["institutions_exclude_default"]=institutionsExcludeList
        #     form_data_dict["institutions_include_default"]=institutionsIncludeList
        #     form_data_dict["experiments_exclude_default"]=experimentsExcludeList
        #     form_data_dict["experiments_include_default"]=experimentsIncludeList

        #     #print(form_data_dict)
        #     form = experimentForm2(form_data_dict,instance=e)

        #     if form.is_valid():
        #         #print("valid form")                                
        #         e=form.save()                               
        #         return JsonResponse({"experiment" : e.json(),"status":"success"}, safe=False)
        #     else:
        #         print("invalid form2")
        #         return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)
    else: #GET             

        return render(request,
                      'staff/experimentSessionView.html',
                      {'form1':experimentSessionForm1(),    
                       'form2':experimentSessionForm2(),                                        
                       'id': id,
                       'session':experiment_sessions.objects.get(id=id)})
        

    