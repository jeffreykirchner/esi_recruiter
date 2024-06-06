from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from main.models import Departments

import logging

#form
class pettyCashForm(forms.Form):

    department =  forms.ModelChoiceField(label="Department",
                                     queryset=Departments.objects.all().order_by('name'),
                                     widget=forms.Select(attrs={"v-model":"pettyCash.department"}))

    startDate = forms.DateTimeField(label="Start Date",
                               input_formats=['%m/%d/%Y'],
                               error_messages={'invalid': 'Format: M/D/YYYY'},                                                                                                           
                               widget = forms.DateTimeInput(attrs={"type":"date",
                                                                   "v-model":"pettyCash.startDate"})) 
                               
    endDate = forms.DateTimeField(label="End Date",
                               input_formats=['%m/%d/%Y'],
                               error_messages={'invalid': 'Format: M/D/YYYY'},                                                                                                           
                               widget = forms.DateTimeInput(attrs={"type":"date",
                                                                   "v-model":"pettyCash.endDate"}))               


    def clean_endDate(self):
        logger = logging.getLogger(__name__) 
        logger.info("Check date range")

        if not 'startDate' in self.cleaned_data:
            raise forms.ValidationError('Start Date must be before End Date.')
        
        if not 'endDate' in self.cleaned_data:
            raise forms.ValidationError('Start Date must be before End Date.')
       
        try:
            startDate = self.cleaned_data['startDate']
            endDate = self.cleaned_data['endDate']

            if startDate > endDate:            
                raise forms.ValidationError("Start Date must be before End Date.")
            else:
                return endDate
        except ValueError:
            raise forms.ValidationError('Invalid Entry')
