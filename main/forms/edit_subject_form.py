
import logging
import re

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from main.models import account_types
from main.models import profile


#form
class EditSubjectForm(forms.ModelForm):

    studentID = forms.CharField(label='Student ID (Leave blank if non-student)', 
                                max_length=25, 
                                required=False, 
                                widget=forms.TextInput(attrs={"v-model":"subject.studentID",}))

    type = forms.ModelChoiceField(label='Account type',
                                  empty_label=None,
                                  queryset=account_types.objects.all(),
                                  widget=forms.Select(attrs={"v-model":"subject.type",}))
    
    pi_eligible = forms.ChoiceField(label='Can be PI',
                                  choices=((1, 'Yes'), (0, 'No')),
                                  widget=forms.Select(attrs={"v-model":"subject.pi_eligible",}))

    studentWorker = forms.ChoiceField(label='Student worker',             
                                      choices=((1, 'Yes'), (0, 'No')),                 
                                      widget=forms.Select(attrs={"v-model":"subject.studentWorker",}))       

    blackballed = forms.ChoiceField(label='Blackballed',
                                    choices=((1, 'Yes'), (0, 'No')),
                                    widget=forms.Select(attrs={"v-model":"subject.blackballed",}))         
    
    paused = forms.ChoiceField(label='Paused',
                               choices=((1, 'Yes'), (0, 'No')),
                               widget=forms.Select(attrs={"v-model":"subject.paused",}))
    
    international_student = forms.ChoiceField(label='International student',
                                    choices=((1, 'Yes'), (0, 'No')),
                                    widget=forms.Select(attrs={"v-model":"subject.international_student",}))
    
    can_paypal = forms.ChoiceField(label='Can use PayPal',
                                    choices=((1, 'Yes'), (0, 'No')),
                                    widget=forms.Select(attrs={"v-model":"subject.can_paypal",}))
    
    can_recruit = forms.ChoiceField(label='Can recruit subjects',
                                    choices=((1, 'Yes'), (0, 'No')),
                                    widget=forms.Select(attrs={"v-model":"subject.can_recruit",}))
    
    disabled = forms.ChoiceField(label='Disabled (cannot login)',
                                 choices=((1, 'Yes'), (0, 'No')),
                                 widget=forms.Select(attrs={"v-model":"subject.disabled",}))

    class Meta:
        model=profile
        fields = ['studentID', 'type', 'pi_eligible', 'can_paypal', 'can_recruit', 'studentWorker', 'blackballed', 
                  'paused', 'international_student', 'disabled']        

    # def clean_studentWorker(self):
    #     logger = logging.getLogger(__name__) 
    #     logger.info("Clean studentWorker")

    #     studentWorker = self.cleaned_data['studentWorker']

    #     if studentWorker == "1":
    #         return 1
    #     elif studentWorker == "0":
    #         return 0
    #     else:
    #         raise forms.ValidationError("Please answer the question.")
        
    # def clean_pi_eligible(self):
    #     logger = logging.getLogger(__name__) 
    #     logger.info("Clean pi_eligible")

    #     pi_eligible = self.cleaned_data['pi_eligible']

    #     if pi_eligible == "1":
    #         return 1
    #     elif pi_eligible == "0":
    #         return 0
    #     else:
    #         raise forms.ValidationError("Please answer the question.")
        
    # def clean_blackballed(self):
    #     logger = logging.getLogger(__name__) 
    #     logger.info("Clean blackballed")

    #     blackballed = self.cleaned_data['blackballed']

    #     if blackballed == "1":
    #         return 1
    #     elif blackballed == "0":
    #         return 0
    #     else:
    #         raise forms.ValidationError("Please answer the question.")
        
    # def clean_paused(self):
    #     logger = logging.getLogger(__name__) 
    #     logger.info("Clean paused")

    #     paused = self.cleaned_data['paused']

    #     if paused == "1":
    #         return 1
    #     elif paused == "0":
    #         return 0
    #     else:
    #         raise forms.ValidationError("Please answer the question.")
    
    # def clean_international_student(self):
    #     logger = logging.getLogger(__name__) 
    #     logger.info("Clean international_student")

    #     international_student = self.cleaned_data['international_student']

    #     if international_student == "1":
    #         return 1
    #     elif international_student == "0":
    #         return 0
    #     else:
    #         raise forms.ValidationError("Please answer the question.")
        
    # def clean_can_paypal(self):
    #     logger = logging.getLogger(__name__) 
    #     logger.info("Clean can_paypal")

    #     can_paypal = self.cleaned_data['can_paypal']

    #     if can_paypal == "1":
    #         return 1
    #     elif can_paypal == "0":
    #         return 0
    #     else:
    #         raise forms.ValidationError("Please answer the question.")
    
    # def clean_can_recruit(self):
    #     logger = logging.getLogger(__name__) 
    #     logger.info("Clean can_recruit")

    #     can_recruit = self.cleaned_data['can_recruit']

    #     if can_recruit == "1":
    #         return 1
    #     elif can_recruit == "0":
    #         return 0
    #     else:
    #         raise forms.ValidationError("Please answer the question.")
    
    # def clean_disabled(self):
    #     logger = logging.getLogger(__name__) 
    #     logger.info("Clean disabled")

    #     disabled = self.cleaned_data['disabled']

    #     if disabled == "1":
    #         return 1
    #     elif disabled == "0":
    #         return 0
    #     else:
    #         raise forms.ValidationError("Please answer the question.")
        