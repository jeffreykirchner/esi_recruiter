'''
consent form model
'''
from django.db import models

class ConsentForm(models.Model):
    '''
    consent form for a session
    '''
    name = models.CharField(max_length = 300, default="", unique=True)         #title of the consent form
    pdf_file = models.FileField(unique=True)                                   #pdf file from the IRB
    signature_required = models.BooleanField(default=True)                     #if true, subject must do digital signature
    agreement_required = models.BooleanField(default=True)                     #if true, subject must agree to consent form to participate

    timestamp = models.DateTimeField(auto_now_add=True)
    updated= models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Consent Form'
        verbose_name_plural = 'Consent Forms'   
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def json(self):
        return{            
            "id" : self.id,
            "name" : self.name,     
            "pdf_file_url" : self.pdf_file.url,
            "signature_required" : self.signature_required,
            "agreement_required" : self.agreement_required,
        }