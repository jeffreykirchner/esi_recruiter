
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.contrib.auth.models import User
from django.db import models

from main.models import experiment_sessions
from main.models import recruitment_parameters

from main.globals import send_mass_email_service

class experiment_session_invitations(models.Model):
    '''
    experiment session inivitation model
    '''
    experiment_session = models.ForeignKey(experiment_sessions, on_delete=models.CASCADE, related_name='experiment_session_invitations')
    recruitment_params = models.ForeignKey(recruitment_parameters, on_delete=models.CASCADE, null=True)

    users = models.ManyToManyField(User, related_name='experiment_session_invitation_users')

    subjectText = models.CharField(max_length=1000, default="")  
    messageText = models.CharField(max_length=10000, default="")  

    mailResultSentCount =  models.IntegerField(default=0)
    mailResultErrorText = models.CharField(max_length=10000, default="")

    timestamp = models.DateTimeField(auto_now_add= True)
    updated = models.DateTimeField(auto_now= True)   

    def __str__(self):
        return "ID: " + str(self.id)

    class Meta:                
        verbose_name = 'Experiment Session Invitations'
        verbose_name_plural = 'Experiment Session Invitations'    
    
    def send_email_invitations(self, memo):
        '''
        send email invitation to all users in this object
        memo: string, note stored in email service about purpose of email
        '''

        user_list = []

        for i in self.users.all().prefetch_related('profile'):
            user_list.append({"email" : i.email,
                              "variables": [{"name" : "first name", "text" : i.first_name},
                                            {"name" : "last name", "text" : i.last_name},
                                            {"name" : "email", "text" : i.email},
                                            {"name" : "recruiter id", "text" : str(i.id)},
                                            {"name" : "student id", "text" : i.profile.studentID},
                                           ]
                            })

        mail_result = send_mass_email_service(user_list,
                                              self.subjectText, 
                                              self.messageText, 
                                              self.messageText, 
                                              memo, 
                                              len(user_list) * 2)
        
        self.mailResultSentCount = mail_result['mail_count']
        self.mailResultErrorText = mail_result['error_message']

        self.save()

        return mail_result
    
    def get_message_text_filled(self, u):
        '''
        return message text filled with variables from u (User)
        '''

        if not u:
            return self.messageText

        t = self.messageText

        t = t.replace("[first name]", u.first_name)
        t = t.replace("[last name]", u.last_name)
        t = t.replace("[email]", u.email)
        t = t.replace("[recruiter id]", str(u.id))
        t = t.replace("[student id]", u.profile.studentID)

        return t
    
    def json(self):
        '''
        json object of model
        '''
        return{
            "id":self.id,
            "subjectText":self.subjectText,
            "messageText":self.messageText,
            "users":[u.profile.json_min() for u in self.users.all()],
            "date_raw":self.timestamp,
            "mailResultSentCount":self.mailResultSentCount,
            "mailResultErrorText":self.mailResultErrorText,
            "recruitment_params":self.recruitment_params.json_displayString(),
        }


#delete recruitment parameters when deleted
@receiver(post_delete, sender=experiment_session_invitations)
def post_delete_recruitment_params(sender, instance, *args, **kwargs):
    if instance.recruitment_params: # just in case user is not specified
        instance.recruitment_params.delete()
