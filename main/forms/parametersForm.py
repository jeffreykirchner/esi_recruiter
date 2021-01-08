from django import forms
from main.models import parameters
from django.contrib.auth.models import User
from django.forms import ModelChoiceField
import pytz

class UserModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
         return obj.get_full_name()

class parametersForm(forms.ModelForm):
    labManager = UserModelChoiceField(label="Lab Manager",
                                     queryset=User.objects.filter(is_staff = True).order_by('last_name','first_name'),
                                     widget=forms.Select(attrs={})) 

    defaultShowUpFee = forms.CharField(label='Default Show-up Fee ($)',
                                       widget=forms.NumberInput(attrs={}))
    
    maxAnnualEarnings = forms.CharField(label='Max Annual Earnings ($)',
                                       widget=forms.NumberInput(attrs={}))
    
    siteURL = forms.CharField(label='Site URL',
                                         widget=forms.TextInput(attrs={"size":"125"}))

    invitationTextSubject = forms.CharField(label='Default Recruitment Email Subject, Single Day',
                                         widget=forms.TextInput(attrs={"size":"125"}))

    invitationText = forms.CharField(label='Default Recruitment Email Text, Single Day',
                                     widget=forms.Textarea(attrs={"rows":"15", "cols":"125"}))

    invitationTextMultiDaySubject = forms.CharField(label='Default Recruitment Email Subject, Multiple Days',
                                         widget=forms.TextInput(attrs={"size":"125"}))

    invitationTextMultiDay = forms.CharField(label='Default Recruitment Email Text, Multiple Days',
                                     widget=forms.Textarea(attrs={"rows":"15", "cols":"125"}))

    cancelationTextSubject = forms.CharField(label='Cancelation Email Subject',
                                         widget=forms.TextInput(attrs={"size":"125"}))

    cancelationText = forms.CharField(label='Cancelation Email Text',
                                     widget=forms.Textarea(attrs={"rows":"15", "cols":"125"}))

    reminderTextSubject = forms.CharField(label='Reminder Email Subject',
                                         widget=forms.TextInput(attrs={"size":"125"}))

    reminderText = forms.CharField(label='Reminder Email Text',
                                     widget=forms.Textarea(attrs={"rows":"15", "cols":"125"}))
    
    deactivationTextSubject = forms.CharField(label='Deactivation Email Subject',
                                         widget=forms.TextInput(attrs={"size":"125"}))

    deactivationText = forms.CharField(label='Deactivation Email Text',
                                     widget=forms.Textarea(attrs={"rows":"15", "cols":"125"}))

    passwordResetTextSubject = forms.CharField(label='Password Reset Email Subject',
                                         widget=forms.TextInput(attrs={"size":"125"}))

    passwordResetText = forms.CharField(label='Password Reset Email Text',
                                     widget=forms.Textarea(attrs={"rows":"15", "cols":"125"}))

    emailVerificationTextSubject = forms.CharField(label='Account Creation Verification Subject',
                                         widget=forms.TextInput(attrs={"size":"125"}))

    emailVerificationResetText = forms.CharField(label='Account Creation Verification Text',
                                     widget=forms.Textarea(attrs={"rows":"15", "cols":"125"}))
    
    consentForm = forms.CharField(label='Consent Form',
                                     widget=forms.Textarea(attrs={"rows":"25", "cols":"125"}))

    subjectTimeZone = forms.ChoiceField(label="Subject Timezone",
                                        choices=[(tz, tz) for tz in pytz.all_timezones])
    
    noShowCutoff = forms.CharField(label='No-Show Count Cutoff',
                                       widget=forms.NumberInput(attrs={"step":"1","min":"1"}))

    noShowCutoffWindow = forms.CharField(label='No-Show Count Window (Days)',
                                       widget=forms.NumberInput(attrs={"step":"1","min":"1"}))

    class Meta:
        model=parameters
        fields = ('__all__')