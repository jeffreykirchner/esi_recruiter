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
    IRB_ID = models.CharField(max_length = 300, default="")                    #The IRB issued ID number
    archived = models.BooleanField(verbose_name="Archived", default=False)     #if true, new sessions cannot use this consent form
    link_text = models.CharField(max_length = 300, default="View Consent Form")                 #text shown to consent form link
    title_text = models.CharField(max_length = 300, default="Informed Consent to Participate in Research")                #text shown at top of card
    agreement_text = models.CharField(max_length = 300, default="I have read the above information, understand it fully and have had any questions regarding the study answered to my satisfaction. I consent to participate in the research and agree to participate in the study.")            #text shown below link

    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

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
            "pdf_file_name" : self.pdf_file.name,
            "signature_required" : self.signature_required,
            "agreement_required" : self.agreement_required,
            "IRB_ID" : self.IRB_ID,
            "archived" : self.archived,
            "link_text" : self.link_text,
            "title_text" : self.title_text,
            "agreement_text" : self.agreement_text,
        }