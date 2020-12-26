from django import forms
from main.models import genders,subject_types,institutions,experiments,locations,accounts,experiment_session_days
from datetime import datetime,timezone
import pytz
from django.utils.timezone import make_aware
import logging

class experimentSessionForm2(forms.ModelForm):
    location = forms.ModelChoiceField(label="Location", 
                                        queryset=locations.objects.all(),
                                        widget = forms.Select(attrs={"v-model":"currentSessionDay.location",
                                                                     "v-on:change":"mainFormChange2"}))                                                               
    date = forms.DateTimeField(label="Date and Time",
                               localize=True,
                               input_formats=['%m/%d/%Y %I:%M %p %z'],
                               error_messages={'invalid': 'Format: M/D/YYYY H:MM am/pm ZZ'},                                                                                                           
                               widget = forms.DateTimeInput(attrs={"v-model":"currentSessionDay.date",                                                                 
                                                                   "v-on:change":"mainFormChange2"}))
    length = forms.CharField(label='Length in Minutes',
                            widget=forms.NumberInput(attrs={"v-model":"currentSessionDay.length",
                                                            "v-on:keyup":"mainFormChange2",
                                                            "v-on:change":"mainFormChange2",
                                                            "v-bind:disabled":"session.confirmedCount > 0"}))
    account = forms.ModelChoiceField(label="Account",
                                            queryset=accounts.objects.all(),
                                            widget=forms.Select(attrs={"v-model":"currentSessionDay.account",
                                                                       "v-on:change":"mainFormChange2"}))
    auto_reminder = forms.ChoiceField(label="Send Reminder Email",                                       
                                       choices=(('true',"Yes"),('false',"No")),                                                   
                                       widget = forms.RadioSelect(attrs={"v-model":"currentSessionDay.auto_reminder",
                                                                         "v-on:change":"mainFormChange2"}))  
    
    enable_time = forms.ChoiceField(label="Enable Meeting Time",                                       
                                       choices=(('true',"Yes"),('false',"No")),                                                   
                                       widget = forms.RadioSelect(attrs={"v-model":"currentSessionDay.enable_time",
                                                                                   "v-on:change":"mainFormChange2"}))

    class Meta:
        model = experiment_session_days
        exclude=['experiment_session','complete','date_end','reminder_email_sent']
    
    def clean_enable_time(self):
        logger = logging.getLogger(__name__)
        logger.info("Clean enable time")

        v = self.data['enable_time']

        if v=='true':
            return True
        elif v=='false':
            return False
        else:
            raise forms.ValidationError('Invalid Entry')
    
    def clean_auto_reminder(self):
        logger = logging.getLogger(__name__)
        logger.info("Clean auto reminder")

        v = self.data['auto_reminder']

        if v=='true':
            return True
        elif v=='false':
            return False
        else:
            raise forms.ValidationError('Invalid Entry')

    #convert to date to utc time zone
    def clean_date(self):
        logger = logging.getLogger(__name__)
        logger.info("Clean Date in session form")
        
        date = self.data['date']

        logger.info(date)

        try:
            date_time_obj = datetime.strptime(date, '%m/%d/%Y %I:%M %p %z')
            logger.info(date_time_obj)
        except ValueError:
            raise forms.ValidationError('Invalid Format: M/D/YYYY H:MM am/pm ZZ')

        return date_time_obj