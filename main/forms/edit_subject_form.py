
import logging
import re

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from main.models import account_types
from main.models import profile


#form
class EditSubjectForm(forms.ModelForm):

    studentID = forms.CharField(label='Student ID (Leave blank if non-student)', max_length=25, required=False)

    type = forms.ModelChoiceField(label='Account type',
                                  empty_label=None,
                                  queryset=account_types.objects.all(),
                                  widget=forms.Select)
    
    pi_eligible = forms.ChoiceField(label='Can be PI',
                                  choices=((True, 'Yes'), (False, 'No')),
                                  widget=forms.Select)

    studentWorker = forms.ChoiceField(label='Student worker',             
                                      choices=((True, 'Yes'), (False, 'No')),                 
                                      widget=forms.Select)       

    blackballed = forms.ChoiceField(label='Blackballed',
                                    choices=((True, 'Yes'), (False, 'No')),
                                    widget=forms.Select)         
    
    paused = forms.ChoiceField(label='Paused',
                                    choices=((True, 'Yes'), (False, 'No')),
                                    widget=forms.Select)
    
    international_student = forms.ChoiceField(label='International student',
                                    choices=((True, 'Yes'), (False, 'No')),
                                    widget=forms.Select)
    
    can_paypal = forms.ChoiceField(label='Can use PayPal',
                                    choices=((True, 'Yes'), (False, 'No')),
                                    widget=forms.Select)
    
    can_recruit = forms.ChoiceField(label='Can recruit subjects',
                                    choices=((True, 'Yes'), (False, 'No')),
                                    widget=forms.Select)
    
    disabled = forms.ChoiceField(label='Disabled (cannot login)',
                                 choices=((True, 'Yes'), (False, 'No')),
                                 widget=forms.Select)

    
    class Meta:
        model=profile
        fields = ['studentID', 'type', 'pi_eligible', 'can_paypal', 'can_recruit', 'studentWorker', 'blackballed', 
                  'paused', 'international_student', 'disabled']        

    def clean_studentWorker(self):
        logger = logging.getLogger(__name__) 
        logger.info("Clean studentWorker")

        studentWorker = self.cleaned_data['studentWorker']

        if studentWorker == "True":
            return True
        elif studentWorker == "False":
            return False
        else:
            raise forms.ValidationError("Please answer the question.")
        
    def clean_pi_eligible(self):
        logger = logging.getLogger(__name__) 
        logger.info("Clean pi_eligible")

        pi_eligible = self.cleaned_data['pi_eligible']

        if pi_eligible == "True":
            return True
        elif pi_eligible == "False":
            return False
        else:
            raise forms.ValidationError("Please answer the question.")
        
    def clean_blackballed(self):
        logger = logging.getLogger(__name__) 
        logger.info("Clean blackballed")

        blackballed = self.cleaned_data['blackballed']

        if blackballed == "True":
            return True
        elif blackballed == "False":
            return False
        else:
            raise forms.ValidationError("Please answer the question.")
        
    def clean_paused(self):
        logger = logging.getLogger(__name__) 
        logger.info("Clean paused")

        paused = self.cleaned_data['paused']

        if paused == "True":
            return True
        elif paused == "False":
            return False
        else:
            raise forms.ValidationError("Please answer the question.")
    
    def clean_international_student(self):
        logger = logging.getLogger(__name__) 
        logger.info("Clean international_student")

        international_student = self.cleaned_data['international_student']

        if international_student == "True":
            return True
        elif international_student == "False":
            return False
        else:
            raise forms.ValidationError("Please answer the question.")
        
    def clean_can_paypal(self):
        logger = logging.getLogger(__name__) 
        logger.info("Clean can_paypal")

        can_paypal = self.cleaned_data['can_paypal']

        if can_paypal == "True":
            return True
        elif can_paypal == "False":
            return False
        else:
            raise forms.ValidationError("Please answer the question.")
    
    def clean_can_recruit(self):
        logger = logging.getLogger(__name__) 
        logger.info("Clean can_recruit")

        can_recruit = self.cleaned_data['can_recruit']

        if can_recruit == "True":
            return True
        elif can_recruit == "False":
            return False
        else:
            raise forms.ValidationError("Please answer the question.")
    
    def clean_disabled(self):
        logger = logging.getLogger(__name__) 
        logger.info("Clean disabled")

        disabled = self.cleaned_data['disabled']

        if disabled == "True":
            return True
        elif disabled == "False":
            return False
        else:
            raise forms.ValidationError("Please answer the question.")
        