
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
    from_email = settings.EMAIL_HOST_USER    

    i = 0
    c = 0
    for s in subjectList:

        if c == 100:
            c = 0
            i += 1
            message_list.append(())

        new_message = s['first_name'] + ",\n\n" + message

        if settings.DEBUG:
            message_list[i] += ((subject, new_message,from_email,["TestSubject" + str(random.randrange(1, 50)) + "@esirecruiter.net"]),)   #use for test emails
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

    from_email = settings.EMAIL_HOST_USER    

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
        link += "profileVerify/" + p.email_confirmed +"/"

        message = params.deactivationText
        message = message.replace("[activation link]",link)
        message = message.replace("[contact email]",params.labManager.email)

        new_message = p.user.first_name + ",\n\n" + message

        if settings.DEBUG:
            message_list[i] += ((subject, new_message,from_email,["TestSubject" + str(random.randrange(1, 50)) + "@esirecruiter.net"]),)   #use for test emails
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

#send email when profile is created or changed
def profileCreateSendEmail(request,u):
    logger = logging.getLogger(__name__) 
    logger.info("Verify Email: ")
    logger.info(u.profile)

    params = parameters.objects.get(id=1)

    u.profile.email_confirmed = get_random_string(length=32)   
    u.profile.save()

    link = params.siteURL       
    link += "profileVerify/" + u.profile.email_confirmed +"/"

    msg_html = render_to_string('profileVerifyEmail.html', {'link': link,'first_name':u.first_name})
    msg_plain = strip_tags(msg_html)

    email_address=""
    if settings.DEBUG:
        email_address = "TestSubject" + str(random.randrange(1, 50)) + "@esirecruiter.net"
    else:
        email_address = u.email

    send_mail(
        'Confirm your email',
        msg_plain,
        settings.DEFAULT_FROM_EMAIL,
        [email_address],
        html_message=msg_html,
        fail_silently=False,
    )