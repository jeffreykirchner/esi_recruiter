import logging

from django import forms

from main.models import IrbStudy

#form
class IrbReportForm(forms.Form):

    irb_study =  forms.ModelChoiceField(label="IRB Study",
                                  required=True,
                                  empty_label=None,
                                  queryset=IrbStudy.objects.all(),
                                  widget=forms.Select(attrs={}))
    
    start_range = forms.DateField(label="Start Range",                                                             
                                  widget=forms.DateTimeInput(attrs={"type":"date",
                                                                    "v-model":"start_range"}))
    
    end_range = forms.DateField(label="Start Range",                                                             
                                  widget=forms.DateTimeInput(attrs={"type":"date",
                                                                    "v-model":"end_range"}))
               