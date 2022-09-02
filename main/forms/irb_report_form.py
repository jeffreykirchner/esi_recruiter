import logging

from django import forms

from main.models import IrbStudy

#form
class IrbReportForm(forms.Form):

    irb_study =  forms.ModelChoiceField(label="IRB Study",
                                  required=True,
                                  empty_label=None,
                                  queryset=IrbStudy.objects.all(),
                                  widget=forms.Select(attrs={"v-model":"irb_study"}))
               