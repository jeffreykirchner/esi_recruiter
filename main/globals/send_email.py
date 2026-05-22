
'''
send email via ESI mass email service
'''
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from smtplib import SMTPException

import logging
import requests
import sys
import json

from django.utils.crypto import get_random_string
from django.conf import settings
from django.utils.html import strip_tags

from main.models import profile
from main.models import Parameters

from main.globals.todays_date import todays_date

def send_mass_email_verify(profile_list, request):
    '''
    send mass deactivation email to current active subjects
    '''
    logger = logging.getLogger(__name__)
    logger.info(f"Send mass verification email to list: {profile_list}")

    params = Parameters.objects.first()

    if len(profile_list) == 0:
        return {"mailCount":0, "errorMessage":"No valid users"}

    for prfl in profile_list:
        prfl.email_confirmed = get_random_string(length=32)
    
    profile.objects.bulk_update(profile_list, ['email_confirmed'])

    user_list = []

    for prfl in profile_list:     
        user_list.append({"email" : prfl.user.email,
                          "variables": [{"name" : "activation link", "text" : f'{params.siteURL}/profileVerify/{prfl.email_confirmed}'},
                                        {"name" : "first name", "text" : prfl.user.first_name},
                                        {"name" : "contact email", "text" : params.labManager.email}]})
            
    memo = 'Bulk account deactivation'

    try:
        return send_mass_email_service(user_list, params.deactivationTextSubject, params.deactivationText,  params.deactivationText, memo, 5)             
    except SMTPException as exc:
        logger.info(f'There was an error sending email: {exc}') 
        return {"mail_count":0, "error_message":str(exc)}

#send email when profile is created or changed
def profile_create_send_email(user):
    logger = logging.getLogger(__name__) 
    logger.info(f"Verify Email: {user.profile}")

    params = Parameters.objects.first()

    user.profile.email_confirmed = get_random_string(length=32)   
    user.profile.save()

    user_list = []
    user_list.append({"email" : user.email,
                      "variables": [{"name" : "activation link", "text" : f'{params.siteURL}/profileVerify/{user.profile.email_confirmed}'},
                                    {"name" : "first name", "text" : user.first_name},
                                    {"name" : "contact email", "text" : params.labManager.email}]})

    memo = f'Verfiy email address for user {user.id}'

    try:
        return send_mass_email_service(user_list, params.emailVerificationTextSubject, params.emailVerificationResetText, params.emailVerificationResetText, memo, 5)             
    except SMTPException as exc:
        logger.info(f'There was an error sending email: {exc}') 
        return {"mail_count":0, "error_message":str(exc)}

def send_daily_report(user_list, email_text, email_text_html):
    '''
    send daily report to specified users
    '''
    logger = logging.getLogger(__name__) 
    logger.info(f"send_daily_report: {user_list}")

    today = todays_date()
    today -= timedelta(days=1)

    user_list_valid = []
    for user in user_list:
        user_list_valid.append({"email" : user.email,
                                "variables": []})
    
    memo = f'Daily email report for {today.strftime("%#m/%#d/%Y")}'

    try:
        return send_mass_email_service(user_list_valid, "Daily Report", email_text, email_text_html, memo, 5)             
    except SMTPException as exc:
        logger.info(f'There was an error sending email: {exc}') 
        return {"mail_count":0, "error_message":str(exc)}

def email_ms_auth() -> bool:
    '''
    check if email service needs a new token
    '''
    logger = logging.getLogger(__name__)
    logger.info("email service auth")

    prm = Parameters.objects.first()

    headers = {"Accept": "application/json",
               "Accept-Language": "en_US"}

    status = "fail"
    if prm.email_ms_access_token != "":
        #try to refresh token if it's expired
        data = {"grant_type":"refresh_token",
                "refresh_token": prm.email_ms_refresh_token,
                "client_id": settings.EMAIL_MS_CLIENT_ID,
                "client_secret": settings.EMAIL_MS_CLIENT_SECRET,}

        req = requests.post(f'{settings.EMAIL_MS_HOST}/o/token/',
                              headers = headers,
                              data = data)

        req_json = req.json()
        prm.email_ms_access_token = req_json.get("access_token", "")
        prm.email_ms_refresh_token = req_json.get("refresh_token", "")
        prm.email_ms_token_expiration = datetime.now() + timedelta(seconds=req_json.get("expires_in", 0))

        prm.save()

        if req.status_code == 200:
            status = "success"
        else:
            logger.info(f'email service auth failed to refresh token: {req_json}')
   
    if status == "fail":
        #no token or failed to refresh, need to login again with username/password
        data = {"grant_type":"password",
                "username": settings.EMAIL_MS_USER_NAME,
                "password": settings.EMAIL_MS_PASSWORD,}

        req = requests.post(f'{settings.EMAIL_MS_HOST}/o/token/',
                              headers = headers,
                              auth=(str(settings.EMAIL_MS_CLIENT_ID), str(settings.EMAIL_MS_CLIENT_SECRET)),
                              data = data)

        req_json = req.json()
        prm.email_ms_access_token = req_json.get("access_token", "")
        prm.email_ms_refresh_token = req_json.get("refresh_token", "")
        prm.email_ms_token_expiration = datetime.now() + timedelta(seconds=req_json.get("expires_in", 0))

        prm.save()

        if req.status_code == 200:
            status = "success"
        else:
            logger.info(f'email service auth failed with username/password: {req_json}')

    # logger.info(f'email_service_auth status code: {req.status_code}')

    if status == "fail":
        # logger.info(f'email service auth failed: {req_json}')
        return False
    
    return True

def send_mass_email_service(user_list, message_subject, message_text, message_text_html, memo, timeout=1200):
    '''
    send mass email through ESI mass pay service
    returns : {mail_count:int, error_message:str}

    :param user_list: List of users to email [{email:email, variables:[{name:""},{text:""}}, ]
    :type user_list: List

    :param message_subject : string subject header of message
    :type message_subject

    :param message_text : message template, variables : [first name]
    :type message_text: string 
    
    :param memo : note about message's purpose
    :type memo: string 

    :param timeout : optionally set the numbe of seconds to wait for response from mail server
    :type int

    '''
    #min time out
    #timeout = max(30, timeout)
    timeout = 30

    logger = logging.getLogger(__name__)

    if hasattr(sys, '_called_from_test'):
        logger.info(f"ESI mass email API: Unit Test")
        return {"mail_count":len(user_list), "error_message":""}

    prm = Parameters.objects.first()

    chunk_size = 5000
    mail_count = 0

    #check for token expiration, refresh will expire in the next 5 minutes to avoid failed requests due to expired token
    if prm.email_ms_token_expiration is None or prm.email_ms_token_expiration < datetime.now(ZoneInfo(prm.subjectTimeZone)) + timedelta(minutes=5):
        logger.info("email service action: token expired, refreshing")
        if not email_ms_auth():
            logger.info("email service action: token refresh failed to refresh")
            return {"mail_count":mail_count, "error_message":"ESI API authorization failed."}
    
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {prm.email_ms_access_token}"}

    for i in range(0, len(user_list), chunk_size):

        user_list_chunk = user_list[i:i + chunk_size]

        data = {"user_list" : user_list_chunk,
                "message_subject" : message_subject,
                "message_text" : strip_tags(message_text).replace("&nbsp;", " "),
                "message_text_html" : message_text_html,
                "memo" : memo}
        
        logger.info(f"ESI mass email API: users({len(user_list_chunk)}): {user_list_chunk}, message_subject : {message_subject}, message_text : {message_text}")

        request_result = {}

        try:
            
            request_result = requests.post(f'{settings.EMAIL_MS_HOST}/send-email/',
                                        json=data,
                                        headers=headers,
                                        timeout=timeout)
                                        
        except requests.Timeout:
            logger.error(f'send_mass_email_service error: Mail service timed out, {data}')
            return {"mail_count":mail_count, "error_message":"Mail service timed out."}
        except requests.ConnectionError:
            logger.error(f'send_mass_email_service error: Could not connect to mail service')
            return {"mail_count":mail_count, "error_message":"Could not connect to mail service."}
        
        if request_result.status_code == 500:        
            logger.warning(f'send_mass_email_service error: {request_result}')
            return {"mail_count":mail_count, "error_message":"Mail service error"}
        
        #check failed auth code
        if request_result.status_code != 201:
            if email_ms_auth():
                return {"mail_count":mail_count, "error_message":"Mail service error, retry email."}
                
            logger.info("esi account action: API authorization failed")
            return {"mail_count":mail_count, "error_message":"ESI API authorization failed."}
    
        try:
            logger.info(f"ESI mass email API response: {request_result.json()}")
        except json.decoder.JSONDecodeError as exc:
            logger.error(f'send_mass_email_service error: Invalid response from mail service, Error {exc}, Result {request_result}')
            return {"mail_count":mail_count, "error_message":"Invalid response from mail service."}

        mail_count += request_result.json()['mail_count']


    return {"mail_count":mail_count, "error_message":""}
