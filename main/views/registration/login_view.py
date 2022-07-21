import logging
import json

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View

from main.forms import loginForm

from main.models import Front_page_notice
from main.models import parameters

class LoginView(View):
    '''
    login view
    '''

    template_name = "registration/login.html"

    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logout(request)

        request.session['redirect_path'] = request.GET.get('next','/')

        p = parameters.objects.first()
        labManager = p.labManager 

        form = loginForm()

        form_ids=[]
        for i in form:
            form_ids.append(i.html_name)

        fpn_list = Front_page_notice.objects.filter(enabled = True)

        return render(request,self.template_name,{"labManager":labManager,
                                                  "form":form,
                                                  "fpn_list":fpn_list,
                                                  "form_ids":form_ids})
    
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''
        logger = logging.getLogger(__name__) 

        request_body = ""
        data = ""

        try:
            request_body = request.body.decode('utf-8')
            data = json.loads(request_body)

            if data["action"] == "login":
                return login_function(request,data)

            return JsonResponse({"response" :  "error"},safe=False)

        except ValueError as err:
            logger.warning(f"loginView: JSON format error, {str(err)}, request_body {request_body}, data {data}")
            return JsonResponse({"response" :  "error"},safe=False)
   
def login_function(request,data):
    logger = logging.getLogger(__name__) 
    #logger.info(data)

    #convert form into dictionary
    form_data_dict = {}             

    for field in data["formData"]:            
        form_data_dict[field["name"]] = field["value"]
    
    f = loginForm(form_data_dict)

    if f.is_valid():

        username = f.cleaned_data['username']
        password = f.cleaned_data['password']

        #logger.info(f"Login user {username}")

        user = authenticate(request, username=username.lower(), password=password)

        if user is not None:
            if not user.is_active:

                logger.error(f"Login user {username} inactive account.")                
                return JsonResponse({"status":"error", "message":"Your account is not active. Contact us for more information."}, safe=False)
            else:
                
                login(request, user) 

                rp = request.session.get('redirect_path','/')        

                logger.info(f"Login user {username} success , redirect {rp}")

                return JsonResponse({"status":"success","redirect_path":rp}, safe=False)
        else:
            logger.warning(f"Login user {username} fail user / pass")
            
            return JsonResponse({"status":"error", "message":"Username or Password is incorrect."}, safe=False)
    else:
        logger.info(f"Login user form validation error")
        return JsonResponse({"status":"validation","errors":dict(f.errors.items())}, safe=False)