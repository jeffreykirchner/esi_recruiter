
'''
send email via ESI mass email service
'''
from smtplib import SMTPException

import logging
import requests

from django.utils.crypto import get_random_string
from django.conf import settings

from main.models import profile, parameters

def sendMassEmail(subjectList, subject, message):
    logger = logging.getLogger(__name__)
    logger.info("Send mass email to list")

    message_list = []
    message_list.append(())
    from_email = getFromEmail()    

    i = 0
    c = 0
    for s in subjectList:

        if c == 100:
            c = 0
            i += 1
            message_list.append(())

        new_message = s['first_name'] + ",\n\n" + message

        if settings.DEBUG:
            s=getTestSubjectEmail()
            message_list[i] += ((subject, new_message,from_email,[s]),)   #use for test emails
        else:
            message_list[i] += ((subject, new_message,from_email,[s['email']]),)  

        c+=1      

    #logger.info(message_list)

    errorMessage = ""
    mailCount=0
    if len(subjectList)>0 :
        try:
            for x in range(i+1):            
                logger.info("Sending Block " + str(x+1) + " of " + str(i+1))
                mailCount += send_mass_mail(message_list[x], fail_silently=False) 
        except SMTPException as e:
            logger.info('There was an error sending email: ' + str(e)) 
            errorMessage = str(e)
    else:
        errorMessage:"The session is empty, no emails sent."

    return {"mailCount":mailCount,"errorMessage":errorMessage}

#send verify email to list, takes query set
def send_mass_email_verify(profile_list, request):
    logger = logging.getLogger(__name__)
    logger.info(f"Send mass verification email to list: {profile_list}")

    params = parameters.objects.first()

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
        return send_mass_email_service(user_list, params.deactivationTextSubject, params.emailVerificationResetText, memo)             
    except SMTPException as exc:
        logger.info(f'There was an error sending email: {exc}') 
        return {"mail_count":0, "error_message":str(exc)}

#send email when profile is created or changed
def profile_create_send_email(request, user):
    logger = logging.getLogger(__name__) 
    logger.info(f"Verify Email: {user.profile}")

    params = parameters.objects.first()

    user.profile.email_confirmed = get_random_string(length=32)   
    user.profile.save()

    user_list = []
    user_list.append({"email" : user.email,
                      "variables": [{"name" : "activation link", "text" : f'{params.siteURL}/profileVerify/{user.profile.email_confirmed}'},
                                    {"name" : "first name", "text" : user.first_name},
                                    {"name" : "contact email", "text" : params.labManager.email}]})

    memo = f'Verfiy email address for user {user.id}'

    try:
        return send_mass_email_service(user_list, params.emailVerificationTextSubject, params.emailVerificationResetText, memo)             
    except SMTPException as exc:
        logger.info(f'There was an error sending email: {exc}') 
        return {"mail_count":0, "error_message":str(exc)}

def send_mass_email_service(user_list, message_subject, message_text, memo):
    '''
    send mass email through ESI mass pay service
    user_list : [{email:email, variables:[{name:""},{text:""}}, ]
    message_subject : string subject header of message
    message_text : string message template, variables : [name]
    memo : string note about message's purpose

    returns : {mail_count:int, error_message:str}
    '''

    data = {"user_list" : user_list,
            "message_subject" : message_subject,
            "message_text" : message_text,
            "memo" : memo}

    logger = logging.getLogger(__name__)
    logger.info(f"ESI mass email API: users: {user_list}, message_subject : {message_subject}, message_text : {message_text}")

    headers = {'Content-Type' : 'application/json', 'Accept' : 'application/json'}

    request_result = requests.post(f'{settings.EMAIL_MS_HOST}/send-email/',
                                   json=data,
                                   auth=(str(settings.EMAIL_MS_USER_NAME), str(settings.EMAIL_MS_PASSWORD)),
                                   headers=headers)
    
    if request_result.status_code == 500:        
        logger.warning(f'send_mass_email_service error: {request_result}')
        return {"mail_count":0, "error_message":"Mail service error"}
    else:
        logger.info(f"ESI mass email API response: {request_result.json()}")

        return request_result.json()