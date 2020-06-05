from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.db.models.functions import Lower
from main.views.forms import userInfoForm
from django.http import Http404
from django.db import IntegrityError

@login_required
@user_is_staff
def userInfo(request,id=None):
    u=User.objects.get(id=id)

    if request.method == 'POST':       

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "updateUser":

            form_data_dict = {}

            for field in data["formData"]:
                form_data_dict[field["name"]] = field["value"]

            form = userInfoForm(form_data_dict)
           
            print(form_data_dict)

            if form.is_valid():
                #print("valid form")                

                u.first_name=form.cleaned_data['first_name']
                u.last_name=form.cleaned_data['last_name']
                u.email=form.cleaned_data['email'].lower()
                u.username=u.email

                u.profile.chapmanID=form.cleaned_data['chapmanID']
                u.profile.gender=form.cleaned_data['gender']
                u.profile.type=form.cleaned_data['type']
                u.profile.blackballed=form.cleaned_data['blackballed']

                try:
                    u.save() 
                except IntegrityError as e:  
                    errorMessage=e.args
                    # print(errorMessage)

                    if errorMessage[0] == "UNIQUE constraint failed: auth_user.username":              
                        return JsonResponse({"status":"fail",
                                             "errors":{"email":["This email address is already in use."]}}, safe=False)
                    else:
                        return JsonResponse({"status":"failSave","message":errorMessage}, safe=False)                

                return JsonResponse({"user" : u.profile.json(),"status":"success"}, safe=False)
            else:
                # print("invalid form1")
                return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

            return JsonResponse({"user" :  u.profile.json()},safe=False) 
        elif data["action"] == "getUser":
           
            return JsonResponse({"user" :  u.profile.json()},safe=False)       
    else:
        e=[]        
            
        ssLt = longTerm.models.session_subject.objects.all().filter(user=u).first()
        ssRe = realEffort.models.session_subject.objects.all().filter(user=u).first()

        formIDs = [i.html_name for i in userInfoForm()]        
        return render(request,'userInfo.html',{"formIDs":formIDs,
                                                "userForm":userInfoForm(initial={'first_name': u.first_name,
                                                                                'last_name': u.last_name,
                                                                                'email':u.email,
                                                                                'chapmanID':u.profile.chapmanID,
                                                                                'type':u.profile.type,
                                                                                'gender':u.profile.gender,
                                                                                'blackballed':u.profile.blackballed})})      

