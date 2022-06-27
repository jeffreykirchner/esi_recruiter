'''
Experiment session form
'''
from datetime import datetime

import logging

from django import forms

from main.models import ConsentForm
from main.models import experiment_sessions

class experimentSessionForm1(forms.ModelForm):
    '''
    Experiment session parameters form
    '''
    consent_form = forms.ModelChoiceField(label='Consent Form',
                                          queryset=ConsentForm.objects.all(),
                                          required=False,
                                          widget=forms.Select(attrs={"v-model":"session.consent_form",
                                                                    }))

    

    class Meta:
        model = experiment_sessions
        fields = ['consent_form']

