'''
Experiment session day form
'''
from datetime import datetime

import logging

from django import forms

from main.models import locations, accounts, experiment_session_days

class experimentSessionForm2(forms.ModelForm):
    '''
    Experiment session parameters form
    '''
    location = forms.ModelChoiceField(label="Location",
                                      queryset=locations.objects.all(),
                                      widget=forms.Select(attrs={"v-model":"currentSessionDay.location",
                                                                 "v-on:change":"mainFormChange2"}))

    date = forms.DateTimeField(label="Date and Time",
                               localize=True,
                               input_formats=['%m/%d/%Y %I:%M %p %z'],
                               error_messages={'invalid': 'Format: M/D/YYYY H:MM am/pm ZZ'},
                               widget=forms.DateTimeInput(attrs={"v-model":"currentSessionDay.date",
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
                                      choices=(('true', "Yes"), ('false', "No")),
                                      widget=forms.RadioSelect(attrs={"v-model":"currentSessionDay.auto_reminder",
                                                                      "v-on:change":"mainFormChange2"}))

    enable_time = forms.ChoiceField(label="Enable Meeting Time",
                                    choices=(('true', "Yes"), ('false', "No")),
                                    widget=forms.RadioSelect(attrs={"v-model":"currentSessionDay.enable_time",
                                                                    "v-on:change":"mainFormChange2",
                                                                    "v-bind:disabled":"session.confirmedCount > 0"}))

    reminder_time = forms.DateTimeField(label="Reminder Date and Time",
                                        localize=True,
                                        input_formats=['%m/%d/%Y %I:%M %p %z'],
                                        error_messages={'invalid': 'Format: M/D/YYYY H:MM am/pm ZZ'},
                                        widget=forms.DateTimeInput(attrs={"v-model":"currentSessionDay.reminder_time",
                                                                          "v-on:change":"mainFormChange2"}))

    custom_reminder_time = forms.ChoiceField(label="Set Custom Reminder Time",
                                             choices=(('true', "Yes"), ('false', "No")),
                                             widget=forms.RadioSelect(attrs={"v-model":"currentSessionDay.custom_reminder_time",
                                                                             "v-on:change":"mainFormChange2"}))

    class Meta:
        model = experiment_session_days
        fields = ['location', 'date', 'length', 'account', 'auto_reminder', 'enable_time', 'reminder_time', 'custom_reminder_time']

    def clean_enable_time(self):
        '''
        clean enable time boolean
        '''
        logger = logging.getLogger(__name__)
        logger.info("Clean enable time")

        val = self.data['enable_time']

        if val == 'true':
            return True

        if val == 'false':
            return False

        raise forms.ValidationError('Invalid Entry')

    def clean_custom_reminder_time(self):
        '''
        clean custom reminder time
        '''
        logger = logging.getLogger(__name__)
        logger.info("Clean custom_reminder_time")

        val = self.data['custom_reminder_time']

        if val == 'true':
            return True

        if val == 'false':
            return False

        raise forms.ValidationError('Invalid Entry')

    def clean_auto_reminder(self):
        '''
        clean auto reminder
        '''
        logger = logging.getLogger(__name__)
        logger.info("Clean auto reminder")

        val = self.data['auto_reminder']

        if val == 'true':
            return True

        if val == 'false':
            return False

        raise forms.ValidationError('Invalid Entry')

    #convert to date to utc time zone
    def clean_date(self):
        '''
        clean date
        '''
        logger = logging.getLogger(__name__)
        logger.info("Clean Date in session form")

        date = self.data['date']

        #logger.info(date)

        try:
            date_time_obj = datetime.strptime(date, '%m/%d/%Y %I:%M %p %z')
            #logger.info(date_time_obj)
        except ValueError:
            raise forms.ValidationError('Invalid Format: M/D/YYYY H:MM am/pm ZZ')

        return date_time_obj

    def clean_reminder_time(self):
        '''
        clean reminder time
        '''
        logger = logging.getLogger(__name__)
        logger.info("Clean reminder_time")

        date_reminder = self.data['reminder_time']
        date = self.data['date']

        #logger.info(date)

        try:
            date_time_obj = datetime.strptime(date_reminder, '%m/%d/%Y %I:%M %p %z')
            #logger.info(date_time_obj)
        except ValueError:
            raise forms.ValidationError('Invalid Format: M/D/YYYY H:MM am/pm ZZ')

        try:
            date_time_obj2 = datetime.strptime(date, '%m/%d/%Y %I:%M %p %z')
            #logger.info(date_time_obj)
        except ValueError:
            raise forms.ValidationError('Reminder must be sooner than session date.')

        if date_time_obj > date_time_obj2:
            raise forms.ValidationError('Reminder must be sooner than session date.')

        return date_time_obj
