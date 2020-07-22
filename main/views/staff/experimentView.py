from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from main.decorators import user_is_staff
from main.models import experiments, \
                        experiment_session_days, \
                        experiment_session_day_users, \
                        experiment_sessions, \
                        accounts, \
                        schools, \
                        institutions, \
                        genders, \
                        parameters
from main.forms import experimentForm1,experimentForm2
from django.http import JsonResponse
from django.core import serializers
from django.forms.models import model_to_dict
import json
from django.db.models import prefetch_related_objects
from django.urls import reverse

#induvidual experiment view
@login_required
@user_is_staff
def experimentView(request,id):
       
    status = ""

    #seeder = Seed.seeder()
    #seeder.add_entity(experiment_sessions, 10)        
    #seeder.execute()            
  

    if request.method == 'POST':
        
        data = json.loads(request.body.decode('utf-8'))         

        try:
            e = experiments.objects.all().prefetch_related("ES").get(id=id)     
        except e.DoesNotExist:
            raise Http404('Experiment Not Found')
        
        if data["status"] == "get":

            p = parameters.objects.get(id=1)
            
            return JsonResponse({"experiment" :  e.json(),
                                 "sessions" : e.json_sessions(),
                                 "parameters" : p.json()}, safe=False)

        elif data["status"] == "update1":

            #print("Form Data:")
            #print(data["formData"])                        

            #un pack form data
            form_data_dict = {} 
            institutionList=[]               

            for field in data["formData"]:            
                if field["name"] == "institution":
                    institutionList.append(field["value"])                
                else:
                    form_data_dict[field["name"]] = field["value"]
            
            form_data_dict["institution"]=institutionList                       

            #print(form_data_dict)
            form = experimentForm1(form_data_dict,instance=e)

            if form.is_valid():
                #print("valid form")                
                e=form.save()               
                return JsonResponse({"experiment" : e.json(),"status":"success"}, safe=False)
            else:
                print("invalid form1")
                return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)                   
        elif data["status"] == "update2":   
            form_data_dict = {} 

            genderList=[]
            subjectTypeList=[]
            institutionsExcludeList=[]
            institutionsIncludeList=[]
            experimentsExcludeList=[]
            experimentsIncludeList=[]

            for field in data["formData"]:            
                if field["name"] == "gender_default":                 
                    genderList.append(field["value"])
                elif field["name"] == "subject_type_default":                 
                    subjectTypeList.append(field["value"])
                elif field["name"] == "institutions_exclude_default":                 
                    institutionsExcludeList.append(field["value"])
                elif field["name"] == "institutions_include_default":                 
                    institutionsIncludeList.append(field["value"])
                elif field["name"] == "experiments_exclude_default":                 
                    experimentsExcludeList.append(field["value"])
                elif field["name"] == "experiments_include_default":                 
                    experimentsIncludeList.append(field["value"])
                else:
                    form_data_dict[field["name"]] = field["value"]

            form_data_dict["gender_default"]=genderList
            form_data_dict["subject_type_default"]=subjectTypeList
            form_data_dict["institutions_exclude_default"]=institutionsExcludeList
            form_data_dict["institutions_include_default"]=institutionsIncludeList
            form_data_dict["experiments_exclude_default"]=experimentsExcludeList
            form_data_dict["experiments_include_default"]=experimentsIncludeList

            #print(form_data_dict)
            form = experimentForm2(form_data_dict,instance=e)

            if form.is_valid():
                #print("valid form")                                
                e=form.save()                               
                return JsonResponse({"experiment" : e.json(),"status":"success"}, safe=False)
            else:
                print("invalid form2")
                return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)
        elif data["status"] == "add":
            #create experiment session, attach to experiment
            es=experiment_sessions()
            es.experiment=e           
            es.save()

            es.setupRecruitment()
            es.save()

            #create experiment session day, attach to session
            esd=experiment_session_days()
            esd.setup(es,[])
            esd.save()

            return JsonResponse({'url':reverse('experimentSessionView',args=(es.id,))},safe=False)
        elif data["status"] == "remove":
            es=experiment_sessions.objects.get(id=data["sid"])

            if es.allowDelete():
                es.delete()

            return JsonResponse({"sessions" : e.json_sessions()}, safe=False)
    else: #GET       

        return render(request,
                      'staff/experimentView.html',
                      {'form1':experimentForm1(),
                       'form2':experimentForm2(),                      
                       'id': id})
        

    