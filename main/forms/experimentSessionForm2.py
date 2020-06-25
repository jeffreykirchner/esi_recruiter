from django import forms
from main.models import genders,subject_types,institutions,experiments,locations,accounts,experiment_session_days

class experimentSessionForm2(forms.ModelForm):
    location = forms.ModelChoiceField(label="Location", 
                                        queryset=locations.objects.all(),
                                        widget = forms.Select(attrs={"v-model":"currentSessionDay.location",
                                                                     "v-on:change":"mainFormChange2"}))                                                               
    date = forms.DateTimeField(label="Date and Time",
                               input_formats=['%m/%d/%Y %I:%M %p'],
                               error_messages={'invalid': 'Format: M/D/YYYY H:MM AM/PM'},                                                                                                           
                               widget = forms.DateTimeInput(attrs={"v-model":"currentSessionDay.date",                                                                 
                                                                   "v-on:change":"mainFormChange2"}))
    length = forms.CharField(label='Length in Minutes',
                            widget=forms.NumberInput(attrs={"v-model":"currentSessionDay.length",
                                                            "v-on:keyup":"mainFormChange2",
                                                            "v-on:change":"mainFormChange2"}))
    account = forms.ModelChoiceField(label="Account",
                                            queryset=accounts.objects.all(),
                                            widget=forms.Select(attrs={"v-model":"currentSessionDay.account",
                                                                       "v-on:change":"mainFormChange2"}))
    auto_reminder = forms.TypedChoiceField(label="Send Reminder Email",                                       
                                       choices=((1,"Yes"),(0,"No")),                                                   
                                       widget = forms.RadioSelect(attrs={"v-model":"currentSessionDay.auto_reminder",
                                                                                "v-on:change":"mainFormChange2"}))  
    canceled = forms.TypedChoiceField(label="Cancel Session",   
                                      choices=((1,"Yes"),(0,"No")),                                                                                
                                      widget = forms.RadioSelect(attrs={"v-model":"currentSessionDay.canceled",
                                                                        "v-on:change":"mainFormChange2"}))

    class Meta:
        model = experiment_session_days
        exclude=['experiment_session']