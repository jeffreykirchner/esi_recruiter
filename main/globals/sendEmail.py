
from django.conf import settings
from django.core.mail import send_mass_mail
from smtplib import SMTPException
import logging
import random
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from main.models import profile,parameters
from django.utils.html import strip_tags
from django.core.mail import send_mail

#send mass email to list,takes a list
def sendMassEmail(subjectList,subject,message):
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
def sendMassEmailVerify(profileList,request):
    logger = logging.getLogger(__name__)
    logger.info("Send mass verification email to list")

    logger.info(profileList)

    message_list = []
    message_list.append(())

    params = parameters.objects.get(id=1)

    subject = params.deactivationTextSubject

    if len(profileList) == 0:
        return {"mailCount":0,"errorMessage":"No valid users"}

    #from_email = settings.EMAIL_HOST_USER    
    from_email = getFromEmail()

    for p in profileList:
        p.email_confirmed = get_random_string(length=32)
    
    profile.objects.bulk_update(profileList, ['email_confirmed'])

    i = 0
    c = 0
    for p in profileList:     

        if c == 100:
            c = 0
            i += 1
            message_list.append(())

        link = params.siteURL      
        link += "/profileVerify/" + p.email_confirmed +"/"

        message = params.deactivationText
        message = message.replace("[activation link]",link)
        message = message.replace("[contact email]",params.labManager.email)

        new_message = p.user.first_name + ",\n\n" + message

        if settings.DEBUG:
            s = getTestSubjectEmail()
            message_list[i] += ((subject, new_message,from_email,[s]),)   #use for test emails
        else:
            message_list[i] += ((subject, new_message,from_email,[p.user.email]),)  

        c+=1
            
    logger.info(message_list)

    errorMessage = ""
    mailCount=0
    try:
        for x in range(i+1):            
            logger.info("Sending Block " + str(x+1) + " of " + str(i+1))
            mailCount += send_mass_mail(message_list[x], fail_silently=False)             
    except SMTPException as e:
        logger.info('There was an error sending email: ' + str(e)) 
        errorMessage = str(e)

    return {"mailCount":mailCount,"errorMessage":errorMessage}

#return the test account email to be used
def getTestSubjectEmail():
    p = parameters.objects.get(id=1)
    s = p.testEmailAccount

    return s

#return the from address
def getFromEmail():    
    return f'"{settings.EMAIL_HOST_USER_NAME}" <{settings.EMAIL_HOST_USER }>'

#send email when profile is created or changed
def profileCreateSendEmail(request,u):
    logger = logging.getLogger(__name__) 
    logger.info("Verify Email: ")
    logger.info(u.profile)

    p = parameters.objects.get(id=1)

    u.profile.email_confirmed = get_random_string(length=32)   
    u.profile.save()

    subject = p.emailVerificationTextSubject

    link = p.siteURL      
    link += "/profileVerify/" + u.profile.email_confirmed +"/"

    message = p.emailVerificationResetText
    message = message.replace("[activation link]",link)
    message = message.replace("[contact email]",p.labManager.email)

    new_message = u.first_name + ",\n\n" + message

    message_list = []
    message_list.append(())

    from_email = getFromEmail()

    if settings.DEBUG:
        s = getTestSubjectEmail()
        message_list[0] += ((subject, new_message,from_email,[s]),)   #use for test emails
    else:
        message_list[0] += ((subject, new_message,from_email,[u.email]),)


    if settings.DEBUG:
        email_address = getTestSubjectEmail()
    else:
        email_address = u.email

    errorMessage = ""
    mailCount=0
    try:
        mailCount = send_mass_mail(message_list[0], fail_silently=False)             
    except SMTPException as e:
        logger.info('There was an error sending email: ' + str(e)) 
        errorMessage = str(e)

    return {"mailCount":mailCount,"errorMessage":errorMessage}