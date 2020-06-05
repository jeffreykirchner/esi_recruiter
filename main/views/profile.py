from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .forms import profileFormUpdate
from .profileCreate import profileCreateSendEmail

from django.conf import settings

import requests
import logging

#user account info
@login_required
def profile(request):
    logger = logging.getLogger(__name__)     

    try:
        status="update"            #either filling out the form or 
        u=request.user
        
        if request.method == 'POST':
            form = profileFormUpdate(request.POST,user=request.user)

            print(request.POST)

            if form.is_valid():                           

                emailVerificationRequired=False

                if u.email != form.cleaned_data['email'].lower():
                    emailVerificationRequired=True
                
                u.first_name=form.cleaned_data['first_name']
                u.last_name=form.cleaned_data['last_name']
                u.email=form.cleaned_data['email'].lower()
                u.username=u.email
                u.profile.chapmanID=form.cleaned_data['chapman_id']
                u.profile.gender=form.cleaned_data['gender']

                if form.cleaned_data['password1']:
                    if form.cleaned_data['password1'] != "":               
                        u.set_password(form.cleaned_data['password1'])                    

                if emailVerificationRequired:
                    u.is_active=False                                
                    profileCreateSendEmail(request,u)

                u.save()
                status="done"
        else:
            form = profileFormUpdate(
                initial={'first_name': request.user.first_name,
                         'last_name': request.user.last_name,
                         'chapman_id': request.user.profile.chapmanID,
                         'email':request.user.email,
                         'gender':request.user.profile.gender.id}
            )

    except u.DoesNotExist:
        raise Http404('Profile not found')

    if settings.ALLOWED_HOSTS[0] == "localhost" or settings.ALLOWED_HOSTS[0] == "127.0.0.1":
        fitBitLink = "https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=" + str(settings.FITBIT_CLIENT_ID) + "&redirect_uri=http%3A%2F%2F" + settings.ALLOWED_HOSTS[0] + "%3A8000%2FfitBit%2F&scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20social%20weight&expires_in=604800&prompt=login%20consent"
    else:
        fitBitLink = "https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=" + str(settings.FITBIT_CLIENT_ID) + "&redirect_uri=https%3A%2F%2F" + settings.ALLOWED_HOSTS[0] + "%3A8000%2FfitBit%2F&scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20social%20weight&expires_in=604800&prompt=login%20consent"
    
    r = getFitbitInfo('https://api.fitbit.com/1/user/-/body/log/weight/date/today.json',request.user)

    #r = getFitbitInfo('https://api.fitbit.com/1/user/-/activities/list.json?afterDate=2020-01-26&sort=desc&limit=10&offset=0',request.user)

    #r = getFitbitInfo('https://api.fitbit.com/1/user/-/activities/date/2020-01-26.json',request.user)
    #r = getFitbitInfo('https://api.fitbit.com/1/user/-/activities/heart/date/2020-02-03/1d/1min.json',request.user)

    logger.info("Profile fitbit test:")
    logger.info(r)

    fitBitAttached = False
    if 'weight' in r:
        fitBitAttached = True
    
    logger.info("Profile fitbit attached:")
    logger.info(fitBitAttached)

    return render(request,'profile.html',{'form': form,
                                          'status':status,
                                          'fitBitLink' : fitBitLink,
                                          'fitBitAttached' : fitBitAttached})    

def getFitbitInfo(url,u):
    logger = logging.getLogger(__name__)         

    r = getFitbitInfo2(url,u)

    #try to reauthorize
    if 'success' in r:        
        headers = {'Authorization': 'Basic ' + str(settings.FITBIT_AUTHORIZATION) ,
                   'Content-Type' : 'application/x-www-form-urlencoded'}
        
        data = {'grant_type' : 'refresh_token',
                'refresh_token' : u.profile.fitBitRefreshToken}    
        
        r = requests.post('https://api.fitbit.com/oauth2/token', headers=headers,data=data).json()

        if 'access_token' in r:
            u.profile.fitBitAccessToken = r['access_token']
            u.profile.fitBitRefreshToken = r['refresh_token']
            u.profile.fitBitUserId = r['user_id']

            u.save()

            logger.info("Fitbit refresh:")
            logger.info(r)
        else:
            logger.info("Fitbit refresh failed:")
            logger.info(r) 

        r = getFitbitInfo2(url,u)
    
    return r

def getFitbitInfo2(url,u):
    logger = logging.getLogger(__name__)     

    headers = {'Authorization': 'Bearer ' + u.profile.fitBitAccessToken,
               'Accept-Language' :	'en_US'}       
    r = requests.get(url, headers=headers).json()

    logger.info("Fitbit request:" + url)
    logger.info(r)

    return r



