'''
consent form model
'''
from django.db import models

class ConsentForm(models.Model):
    '''
    consent form for a session
    '''
    name = models.CharField(max_length = 300, default="", unique=True)
    pdf_file = models.FileField(unique=True)

    timestamp = models.DateTimeField(auto_now_add=True)
    updated= models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Consent Form'
        verbose_name_plural = 'Consent Forms'   
    
    def __str__(self):
        return self.name
    
    def json(self):
        return{            
            "id" : self.id,
            "name" : self.name,     
            "pdf_file_name" : self.pdf_file.name,
        }