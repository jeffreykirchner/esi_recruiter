import logging
import json

from django.shortcuts import render
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.db.models import CharField, Q, F, Value as V
from django.urls import reverse
from django.http import JsonResponse

from django.views.generic import View
from django.utils.decorators import method_decorator

from main.models import account_types
from main.models import profile
from main.models import help_docs

from main.globals import profile_create_send_email
from main.forms import profileForm

class ProfileCreate(View):
    '''
    create new profile
    '''

    template_name = "registration/profileCreate.html"

    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logger = logging.getLogger(__name__)

        logout(request)
        
        form = profileForm()

        #logger.info(reverse('profile'))
        try:
            helpText = help_docs.objects.annotate(rp = V(reverse('profile2'),output_field=CharField()))\
                                        .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
            helpText = "No help doc was found."

        form_ids=[]
        for i in form:
            form_ids.append(i.html_name)

        return render(request, self.template_name,{'form': form,
                                                   'helpText':helpText,
                                                   'form_ids':form_ids})

    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''
        logger = logging.getLogger(__name__)

        #check that request id json formatted
        try:
            request_body = None
            request_body = request.body.decode('utf-8')
            data = json.loads(request_body)
        except Exception  as e:  
           logger.warning(f"Profile create post json error: {request_body}, Exception: {e}") 
           return JsonResponse({"status" :  "error"}, safe=False)

        #check for correct action
        action = data.get("action", "fail")

        if action == "create":
            return createUser(request, data)

        #valid action not found
        logger.warning(f"Profile create post error: {data}")
        return JsonResponse({"status" : "error"}, safe=False)

def createUser(request, data):
    logger = logging.getLogger(__name__) 
    logger.info("Create User")

    form_data_dict = {}             

    for field in data["formData"]:            
        form_data_dict[field["name"]] = field["value"]

        #remove caps from email form
        if field["name"] == "email":
            form_data_dict["email"] = form_data_dict["email"].strip().lower()

    
    f = profileForm(form_data_dict)

    if f.is_valid():
        
        u = profileCreateUser(f.cleaned_data['email'].strip().lower(),
                                    f.cleaned_data['email'].strip().lower(),
                                    f.cleaned_data['password1'],
                                    f.cleaned_data['first_name'].strip().capitalize(),
                                    f.cleaned_data['last_name'].strip().capitalize(),
                                    f.cleaned_data['chapman_id'].strip(),
                                    f.cleaned_data['gender'],
                                    f.cleaned_data['phone'].strip(),
                                    f.cleaned_data['major'],
                                    f.cleaned_data['subject_type'],
                                    f.cleaned_data['studentWorker'],
                                    True,
                                    account_types.objects.get(id=2))

        profile_create_send_email(u)

        u.profile.setup_email_filter()

        #log new user in
        #user = authenticate(request, username=u.username, password=u.password)
        login(request, u) 
         
        return JsonResponse({"status":"success"}, safe=False)

    else:
        logger.info(f"createUser validation error")
        return JsonResponse({"status":"error", "errors":dict(f.errors.items())}, safe=False)


def profileCreateUser(username, email, password, firstName, lastName, studentID, 
                      gender, phone, major, subject_type, studentWorker, isActive, 
                      accountType):

    logger = logging.getLogger(__name__) 

    u = User.objects.create_user(username=username,
                                 email=email,
                                 password=password,                                         
                                 first_name=firstName,
                                 last_name=lastName)

    #u.is_active = isActive   
    u.save()

    p = profile(user=u,
                studentID=studentID,
                gender=gender,
                type=accountType,
                phone=phone,
                major=major,
                subject_type=subject_type,
                studentWorker=studentWorker)

    logger.info("Create Profile: ")
    logger.info(p)

    p.save()
    u.save()

    return u