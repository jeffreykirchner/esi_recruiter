
import logging
import re

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from main.models import account_types
from main.models import profile


#form
class EditSubjectForm(forms.ModelForm):

    chapman_id = forms.CharField(label='Student ID (Leave blank if non-student)', max_length=25, required=False)

    type = forms.ModelChoiceField(label='Account type',
                                  queryset=account_types.objects.all(),
                                  widget=forms.Select)

    studentWorker = forms.ChoiceField(label='Student worker?',             
                                      choices=(('Yes', 'Yes'), ('No', 'No')),                 
                                      widget=forms.Select)       

    blackballed = forms.ChoiceField(label='Blackballed?',
                                    choices=(('Yes', 'Yes'), ('No', 'No')),
                                    widget=forms.Select)         
    
    paused = forms.ChoiceField(label='Paused?',
                                    choices=(('Yes', 'Yes'), ('No', 'No')),
                                    widget=forms.Select)
    
    international_student = forms.ChoiceField(label='International student?',
                                    choices=(('Yes', 'Yes'), ('No', 'No')),
                                    widget=forms.Select)
    
    class Meta:
        model=profile
        fields = ['chapman_id', 'type', 'studentWorker', 'blackballed', 'paused', 'international_student']        


    def clean_studentWorker(self):
        logger = logging.getLogger(__name__) 
        logger.info("Clean studentWorker")

        studentWorker = self.cleaned_data['studentWorker']

        if studentWorker == "Yes":
            return True
        elif studentWorker == "No":
            return False
        else:
            raise forms.ValidationError("Please answer the question.")
        
    def clean_blackballed(self):
        logger = logging.getLogger(__name__) 
        logger.info("Clean blackballed")

        blackballed = self.cleaned_data['blackballed']

        if blackballed == "Yes":
            return True
        elif blackballed == "No":
            return False
        else:
            raise forms.ValidationError("Please answer the question.")
        
    def clean_paused(self):
        logger = logging.getLogger(__name__) 
        logger.info("Clean paused")

        paused = self.cleaned_data['paused']

        if paused == "Yes":
            return True
        elif paused == "No":
            return False
        else:
            raise forms.ValidationError("Please answer the question.")
    
    def clean_international_student(self):
        logger = logging.getLogger(__name__) 
        logger.info("Clean international_student")

        international_student = self.cleaned_data['international_student']

        if international_student == "Yes":
            return True
        elif international_student == "No":
            return False
        else:
            raise forms.ValidationError("Please answer the question.")