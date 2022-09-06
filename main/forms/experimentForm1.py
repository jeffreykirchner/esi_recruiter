import logging

from tinymce.widgets import TinyMCE

from django import forms
from django.contrib.auth.models import User

from main.models import schools
from main.models import accounts
from main.models import institutions
from main.models import experiments
from main.models import ConsentForm

class experimentForm1(forms.ModelForm):   
    '''
    edit experiment parmeters
    '''
    def __init__(self, *args, **kwargs):
        super(experimentForm1, self).__init__(*args, **kwargs)

        self.fields['budget_default'].label_from_instance = self.budget_label_from_instance

    title = forms.CharField(label='Title',
                            widget=forms.TextInput(attrs={"v-model":"experiment.title",
                                                          "v-on:keyup":"mainFormChange1"}))
    experiment_manager = forms.CharField(label='Manager(s)',
                                         widget=forms.TextInput(attrs={"v-model":"experiment.experiment_manager",
                                                                       "v-on:keyup":"mainFormChange1"}))
    
    budget_default = forms.ModelChoiceField(label='Budget (default)',
                                                  queryset=User.objects.filter(profile__type__id=1, is_active=True),
                                                  required=False,
                                                  widget=forms.Select(attrs={"v-model":"experiment.budget_default",
                                                                             "v-on:change":"mainFormChange1"}))

    experiment_pi = forms.ModelChoiceField(label='Primary Investigator',
                                           queryset=User.objects.filter(profile__type__id=1, is_active=True),
                                           required=False,
                                           widget=forms.Select(attrs={"v-model":"experiment.experiment_pi",
                                                                      "v-on:change":"mainFormChange1"}))

    length_default = forms.CharField(label='Length in Minutes (default)',
                                                  widget=forms.NumberInput(attrs={"v-model":"experiment.length_default",
                                                                                  "v-on:keyup":"mainFormChange1",
                                                                                  "v-on:change":"mainFormChange1"}))

    consent_form_default = forms.ModelChoiceField(label='Consent Form (default)',
                                                  queryset=ConsentForm.objects.filter(archived=False),
                                                  required=False,
                                                  widget=forms.Select(attrs={"v-model":"experiment.consent_form_default",
                                                                             "v-on:change":"mainFormChange1"}))

    notes = forms.CharField(label='Notes',
                            widget=forms.Textarea(attrs={"v-model":"experiment.notes",
                                                         "v-on:keyup":"mainFormChange1",
                                                         "rows":"12"}),
                            required=False)

    school = forms.ModelChoiceField(queryset=schools.objects.all(),
                                    widget=forms.Select(attrs={"v-model":"experiment.school",
                                                               "v-on:change":"mainFormChange1"}))
    
    account_default = forms.ModelChoiceField(label="Account (default)",
                                            queryset=accounts.objects.filter(archived=False),
                                            widget=forms.Select(attrs={"v-model":"experiment.account_default",
                                                                       "v-on:change":"mainFormChange1"}))

    showUpFee = forms.CharField(label='Show-up Fee ($)', 
                                            widget=forms.NumberInput(attrs={"v-model":"experiment.showUpFee",
                                                                            "v-on:keyup":"mainFormChange1",
                                                                            "v-on:change":"mainFormChange1"}))

    institution = forms.ModelMultipleChoiceField(label="",
                                                 queryset=institutions.objects.all().order_by("name"),
                                                 widget = forms.CheckboxSelectMultiple(attrs={"v-model":"experiment.institution",
                                                                                      "v-on:change":"mainFormChange1",
                                                                                      "class":"selectpicker",
                                                                                      "size":"13",
                                                                                      "v-bind:disabled":"experiment.confirmationFound === true"}))    

    invitationText = forms.CharField(label='Recruitment Email',
                                     widget=TinyMCE(attrs={"v-model":"experiment.invitationText",
                                                           "v-on:keyup":"mainFormChange1",
                                                           "plugins": "link image code",
                                                           "rows":"12"}))

    reminderText = forms.CharField(label='Reminder Email',
                                   widget=TinyMCE(attrs={"v-model":"experiment.reminderText",
                                                         "v-on:keyup":"mainFormChange1",
                                                         "plugins": "link image code",
                                                         "rows":"12"}))               

    survey = forms.ChoiceField(label="Online Survey",
                                    choices=(('true', "Yes"), ('false', "No")),
                                    widget=forms.Select(attrs={"v-model":"experiment.survey",
                                                                    "v-on:change":"mainFormChange1",
                                                                    "v-bind:disabled":"experiment.confirmationFound === true"}))                                                                                                                                                                                                                                                    

    class Meta:
        model=experiments
        #fields = ['id','title', 'experiment_manager', 'actual_participants','registration_cutoff','notes','school','account','department']        
        exclude=['recruitment_params_default']

    @staticmethod
    def budget_label_from_instance(obj):
        return f"{obj.last_name}, {obj.first_name}"

    def clean_length_default(self):
        length_default = self.data['length_default']

        try:
            if int(length_default) < 0:
                raise forms.ValidationError('Must be greater than zero')
        except ValueError:
            raise forms.ValidationError('Invalid Entry')

        return length_default
    
    def clean_survey(self):
        '''
        clean survey boolean
        '''
        logger = logging.getLogger(__name__)
        logger.info("Clean survey")

        val = self.data['survey']

        if val == 'true':
            return True

        if val == 'false':
            return False

        raise forms.ValidationError('Invalid Entry')