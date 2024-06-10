'''
Experiment session form
'''

from django import forms
from django.contrib.auth.models import User

from main.models import ConsentForm
from main.models import ExperimentSessions

class experimentSessionForm1(forms.ModelForm):
    '''
    Experiment session parameters form
    '''

    #change budget form label
    def __init__(self, *args, **kwargs):
        super(experimentSessionForm1, self).__init__(*args, **kwargs)

        self.fields['budget'].label_from_instance = self.budget_label_from_instance

    consent_form = forms.ModelChoiceField(label='Consent Form',
                                          queryset=ConsentForm.objects.filter(archived=False),
                                          required=False,
                                          widget=forms.Select(attrs={"v-model":"session.consent_form",
                                                                     "v-bind:disabled":"session.allowEdit === false",
                                                                    }))
    
    budget = forms.ModelChoiceField(label='Budget',
                                    queryset=User.objects.filter(profile__type__id=1, profile__pi_eligible=True).order_by('last_name','first_name'),
                                    required=False,
                                    widget=forms.Select(attrs={"v-model":"session.budget",
                                                               }))

    incident_occurred = forms.ChoiceField(label='IRB Incident Occurred',
                                          required=False,
                                          choices=((1, 'Yes'), (0,'No' )),
                                          widget=forms.Select(attrs={"v-model":"session.incident_occurred",}))

    special_instructions = forms.CharField(label='Special Instructions for Subjects, i.e., Zoom Meeting',
                                           required=False,
                                           widget=forms.TextInput(attrs={"v-model":"session.special_instructions",
                                                                         "placeholder":"Leave blank for no instructions"}))

    class Meta:
        model = ExperimentSessions
        fields = ['consent_form', 'budget', 'incident_occurred', 'special_instructions']

    @staticmethod
    def budget_label_from_instance(obj):
        return f"{obj.last_name}, {obj.first_name}"