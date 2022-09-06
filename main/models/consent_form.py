'''
consent form model
'''
from tinymce.models import HTMLField

from django.db import models
from django.core.files.base import ContentFile

from main.models import IrbStudy

class ConsentForm(models.Model):
    '''
    consent form for a session
    '''
    irb_study = models.ForeignKey(IrbStudy, on_delete=models.CASCADE, related_name='consent_forms', null=True, blank=True, verbose_name="IRB Study")

    name = models.CharField(max_length = 300, default="", unique=True)         #title of the consent form
    pdf_file = models.FileField()                                              #pdf file from the IRB
    signature_required = models.BooleanField(default=True)                     #if true, subject must do digital signature
    agreement_required = models.BooleanField(default=True)                     #if true, subject must agree to consent form to participate
    IRB_ID = models.CharField(max_length = 300, default="")                    #The IRB issued ID number
    archived = models.BooleanField(verbose_name="Archived", default=False)     #if true, new sessions cannot use this consent form
    link_text = models.CharField(max_length = 300, default="View Consent Form")                 #text shown to consent form link
    title_text = models.CharField(max_length = 300, default="Informed Consent to Participate in Research")                #text shown at top of card
    agreement_text = models.CharField(max_length = 300, default="I have read the above information, understand it fully and have had any questions regarding the study answered to my satisfaction. I consent to participate in the research and agree to participate in the study.")            #text shown below link
    submit_button_text = models.CharField(max_length = 100, default="I consent to participate")            #text shown below link
    consent_form_text = HTMLField(verbose_name="Consent Form Text", default="")

    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Consent Screen'
        verbose_name_plural = 'Consent Screens'   
        ordering = ['name']
    
    def __str__(self):
        return self.name

    def from_dict(self, values_dict, source_pdf_file):
        '''
        copy values from another consent form 
        '''
        
        self.name = f'{values_dict["name"]} (copy)'
        self.pdf_file = source_pdf_file
        self.signature_required = values_dict["signature_required"]
        self.agreement_required = values_dict["agreement_required"]
        self.IRB_ID = values_dict["IRB_ID"]
        self.archived = values_dict["archived"]
        self.link_text = values_dict["link_text"]
        self.title_text = values_dict["title_text"]
        self.agreement_text = values_dict["agreement_text"]
        self.submit_button_text = values_dict["submit_button_text"]
        self.consent_form_text = values_dict["consent_form_text"]

        self.save()
    
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
            "submit_button_text" : self.submit_button_text,
            "consent_form_text" : self.consent_form_text,
        }