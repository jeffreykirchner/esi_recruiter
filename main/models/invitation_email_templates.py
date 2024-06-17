from tinymce.models import HTMLField

from django.db import models

class InvitationEmailTemplates(models.Model):
    '''
    experiment email invitation template
    '''
    name = models.CharField(verbose_name="Subject Text", max_length=1000, default="")           #template name
    # subject_text = models.CharField(verbose_name="Subject Text", max_length = 1000,default = "")   #email subject
    body_text = HTMLField(verbose_name="Body Text", default="")        #email text

    enabled = models.BooleanField(default=True)

    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        
        verbose_name = 'Invitation Email Template'
        verbose_name_plural = 'Invitation Email Templates'
    
    def json(self):
        return {
            "id" : self.id,
            "name":self.name,
            "subject_text" : self.subject_text,
            "body_text" : self.body_text,
            "enabled" : self.enabled,
        }
        

