import logging
import json

from django.shortcuts import render

from django.views import View
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse

class ProfileVerify(View):
    '''
    verify email address
    '''

    template_name = "registration/profileVerify.html"

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        status="update"
        token = kwargs['token']

        #check for correct token
        u = request.user
        failed = not check_valid_token(u, token)

        #check that user is not already verified
        emailVerified = True
        if u.profile.email_confirmed != 'yes':
            emailVerified = False

        return render(request, self.template_name,{'emailVerified':emailVerified,
                                                   'failed':failed,    
                                                   'token':token,
                                                   'user':u,
                                                   'status':status}) 

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        data = json.loads(request.body.decode('utf-8'))
        token = kwargs['token']

        if data["action"] == "verifyEmail":
            return verifyEmail(request, data, token)        

        return JsonResponse({"status":"fail"}, safe=False)

def check_valid_token(u, token):
    '''
    check that token is valid
    u:user
    token:email validation token
    '''

    if token != u.profile.email_confirmed or \
       u.profile.email_confirmed == 'no':

        return False
    
    return True

def verifyEmail(request, data, token):
    '''
    verify user's email address
    '''
    logger = logging.getLogger(__name__)
    logger.info(f"Verify email: {data} token {token}")

    emailVerified = False
    failed = False

    #check token is correct
    if not check_valid_token(request.user, token):
        failed=True

    #if valid token confirm email
    if not failed:
        try:

            u=request.user                
            #u.is_active=True
            u.profile.email_confirmed = "yes"
            u.profile.paused = False
            u.profile.save()
            u.save()  

            emailVerified = True  

        except ObjectDoesNotExist:
            print("Failed to validate email")
            emailVerified = False
            failed = False

    return JsonResponse({'emailVerified':emailVerified,
                         'failed':failed,}, safe=False)