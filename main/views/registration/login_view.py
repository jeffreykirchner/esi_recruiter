import logging
import json
import pyotp

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
        two_factor = data["two_factor_code"]

        #logger.info(f"Login user {username}")

        user = authenticate(request, username=username.lower(), password=password)

        if user is not None:
            if not user.is_active:

                logger.error(f"Login user {username} inactive account.")                
                return JsonResponse({"status":"error", "message":"Your account is not active. Contact us for more information."}, safe=False)
            else:
                
                #if user can use paypal require two factor code
                if user.profile.mfa_required and two_factor == "":
                    if user.profile.mfa_hash == "" or user.profile.mfa_hash == None:
                        #user has not setup two factor code
                        user.profile.mfa_hash = pyotp.random_base32()
                        user.profile.save()
                        two_factor_uri = pyotp.totp.TOTP(user.profile.mfa_hash).provisioning_uri(user.username,issuer_name="ESI Recruiter")
                        return JsonResponse({"status":"two_factor_setup", 
                                             "message":"Two factor setup required.",
                                             "two_factor_uri":two_factor_uri,
                                             "two_factor_hash":user.profile.mfa_hash}, safe=False)
                    else:    
                        #if user has two factor code enabled, return two factor code required
                       
                        return JsonResponse({"status":"two_factor", "message":"Two factor code required."}, safe=False)
                #if user can use paypal and two factor code is provided verify it
                elif user.profile.mfa_required and two_factor != "":
                    totp = pyotp.TOTP(user.profile.mfa_hash)

                    if not totp.verify(two_factor):
                        return JsonResponse({"status":"error", "message":"Invalid Code"}, safe=False)


                #standard user, no two factor code required
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