from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from main.models import departments

import logging

#form
class pettyCashForm(forms.Form):

    departments =  forms.ModelChoiceField(label="Department",
                                     queryset=departments.objects.all(),
                                     widget=forms.Select(attrs={"v-model":"pettyCash.department"}))
    startDate = forms.DateTimeField(label="Start Date",
                               localize=True,
                               input_formats=['%m/%d/%Y %I:%M %p %z'],
                               error_messages={'invalid': 'Format: M/D/YYYY H:MM am/pm ZZ'},                                                                                                           
                               widget = forms.DateTimeInput(attrs={"v-model":"pettyCash.startDate"})) 
    endDate = forms.DateTimeField(label="Start Date",
                               localize=True,
                               input_formats=['%m/%d/%Y %I:%M %p %z'],
                               error_messages={'invalid': 'Format: M/D/YYYY H:MM am/pm ZZ'},                                                                                                           
                               widget = forms.DateTimeInput(attrs={"v-model":"pettyCash.startDate"}))               


    # def clean_studentWorker(self):
    #     logger = logging.getLogger(__name__) 
    #     logger.info("Clean studentWorker")

    #     studentWorker = self.cleaned_data['studentWorker']

    #     if studentWorker == "Yes":
    #         return True
    #     elif studentWorker == "No":
    #         return False
    #     else:
    #         raise forms.ValidationError("Please answer the question.")
