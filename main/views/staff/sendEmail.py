
from django.conf import settings
from django.core.mail import send_mass_mail
from smtplib import SMTPException
import logging
import random
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from main.models import profile
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

        if settings.DEBUG:
            message_list[i] += ((subject, message,from_email,["TestSubject" + str(random.randrange(1, 50)) + "@esirecruiter.net"]),)   #use for test emails
        else:
            message_list[i] += ((subject, message,from_email,[s['email']]),)  

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
    logger.info("Send mass email to list")

    logger.info(profileList)

    message_list = []
    message_list.append(())

    if len(profileList) == 0:
        return {"mailCount":0,"errorMessage":"No valid users"}

    from_email = settings.EMAIL_HOST_USER    

    for p in profileList:
        p.emailConfirmed = get_random_string(length=32)
    
    profile.objects.bulk_update(profileList, ['emailConfirmed'])

    i = 0
    c = 0
    for p in profileList:     

        if c == 100:
            c = 0
            i += 1
            message_list.append(())

        link = request.get_host()      
        link += "/profileVerify/" + p.emailConfirmed +"/"

        message ="Your account has been disabled.\r\nTo re-activate please confirm your email:\r\n"+ link

        if settings.DEBUG:
            message_list[i] += (("ESI Account Disabled", message,from_email,["TestSubject" + str(random.randrange(1, 50)) + "@esirecruiter.net"]),)   #use for test emails
        else:
            message_list[i] += (("ESI Account Disabled", message,from_email,[p.user.email]),)  

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

    u.profile.emailConfirmed = get_random_string(length=32)   
    u.profile.save()

    link = request.get_host()      
    link += "/profileVerify/" + u.profile.emailConfirmed +"/"

    msg_html = render_to_string('profileVerifyEmail.html', {'link': link})
    msg_plain = strip_tags(msg_html)
    send_mail(
        'Confirm your email',
        msg_plain,
        settings.DEFAULT_FROM_EMAIL,
        [u.email],
        html_message=msg_html,
        fail_silently=False,
    )