from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from main.models import departments

import logging

#form
class studentReportForm(forms.Form):
    studentReport_nra = forms.TypedChoiceField(label="Subjects that are nonresident alien?",                                       
                                       choices=[(1,"Yes"),(0,"No, any subjects.")],                                                  
                                       widget = forms.RadioSelect(attrs={"v-model":"studentReport.studentReport_nra"}))

    studentReport_gt600 = forms.TypedChoiceField(label="Subjects earning at least $[[maxAnnualEarnings]] in total?",                                       
                                       choices=[(1,"Yes"),(0,"No, any earnings.")],                                                  
                                       widget = forms.RadioSelect(attrs={"v-model":"studentReport.studentReport_gt600"}))

    studentReport_studentWorkers = forms.TypedChoiceField(label="Student workers only?",                                       
                                       choices=[(1,"Yes"),(0,"No, any type.")],                                                 
                                       widget = forms.RadioSelect(attrs={"v-model":"studentReport.studentReport_studentWorkers"}))

    studentReport_startDate = forms.DateTimeField(label="Start Date",                               
                               input_formats=['%m/%d/%Y'],
                               error_messages={'invalid': 'Format: MM/DD/YYYY'},                                                                                                           
                               widget = forms.DateTimeInput(attrs={"v-model":"studentReport.studentReport_startDate"})) 
                               
    studentReport_endDate = forms.DateTimeField(label="End Date",                               
                               input_formats=['%m/%d/%Y'],
                               error_messages={'invalid': 'Format: MM/DD/YYYY'},                                                                                                           
                               widget = forms.DateTimeInput(attrs={"v-model":"studentReport.studentReport_endDate"}))               


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
