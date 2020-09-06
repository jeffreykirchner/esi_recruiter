from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from main.models import departments

import logging

#form
class studentReportForm(forms.Form):

    studentReport_startDate = forms.DateTimeField(label="Start Date",
                               localize=True,
                               input_formats=['%m/%d/%Y %I:%M %p %z'],
                               error_messages={'invalid': 'Format: M/D/YYYY H:MM am/pm ZZ'},                                                                                                           
                               widget = forms.DateTimeInput(attrs={"v-model":"pettyCash.startDate"})) 
                               
    studentReport_endDate = forms.DateTimeField(label="End Date",
                               localize=True,
                               input_formats=['%m/%d/%Y %I:%M %p %z'],
                               error_messages={'invalid': 'Format: M/D/YYYY H:MM am/pm ZZ'},                                                                                                           
                               widget = forms.DateTimeInput(attrs={"v-model":"pettyCash.endDate"}))               


    def clean_studentReport_endDate(self):
        logger = logging.getLogger(__name__) 
        logger.info("Check date range")

        if not 'studentReport_startDate' in self.cleaned_data:
            raise forms.ValidationError('Start Date must be before End Date.')
        
        if not 'studentReport_endDate' in self.cleaned_data:
            raise forms.ValidationError('Start Date must be before End Date.')
       
        try:
            startDate = self.cleaned_data['studentReport_startDate']
            endDate = self.cleaned_data['studentReport_endDate']

            if startDate > endDate:            
                raise forms.ValidationError("Start Date must be before End Date.")
            else:
                return endDate
        except ValueError:
            raise forms.ValidationError('Invalid Entry')
