import pytz

from tinymce.widgets import TinyMCE

from django import forms
from django.contrib.auth.models import User
from django.forms import ModelChoiceField

from main.models import parameters

class UserModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
         return obj.get_full_name()

class parametersForm(forms.ModelForm):
    '''
    site parameters admin form
    '''
    labManager = UserModelChoiceField(label="Lab Manager",
                                      queryset=User.objects.filter(is_staff = True).order_by('last_name','first_name'),
                                      widget=forms.Select(attrs={})) 

    defaultShowUpFee = forms.CharField(label='Default Show-up Fee ($)',
                                       widget=forms.NumberInput(attrs={}))
    
    maxAnnualEarnings = forms.CharField(label='Max Annual Earnings ($)',
                                        widget=forms.NumberInput(attrs={}))

    max_invitation_block_size = forms.CharField(label='Max Invitation Block Size',
                                                widget=forms.NumberInput(attrs={}))
    
    siteURL = forms.CharField(label='Site URL',
                              widget=forms.TextInput(attrs={"size":"125"}))
    
    testEmailAccount = forms.CharField(label='Test Email Account',
                                       widget=forms.TextInput(attrs={"size":"125"}))
    
    paypal_email_subject = forms.CharField(label='PayPal mass pay email subject',
                                           widget=forms.TextInput(attrs={"size":"125"}))

    paypal_email_body = forms.CharField(label='PayPal mass pay email body: <subject_name>, <text>',
                                        widget=forms.TextInput(attrs={"size":"125"}))

    invitationTextSubject = forms.CharField(label='Recruitment Email, Subject',
                                            widget=forms.TextInput(attrs={"size":"125"}))

    cancelationTextSubject = forms.CharField(label='Cancelation Email, Subject',
                                             widget=forms.TextInput(attrs={"size":"125"}))

    cancelationText = forms.CharField(label='Cancelation Email, Text',
                                      widget=TinyMCE(attrs={"rows":10, "cols":200, "plugins": "link image code"}))

    reminderTextSubject = forms.CharField(label='Reminder Email, Subject',
                                          widget=forms.TextInput(attrs={"size":"125"}))

    reminderText = forms.CharField(label='Reminder Email, Text',
                                   widget=TinyMCE(attrs={"rows":10, "cols":200, "plugins": "link image code"}))
    
    deactivationTextSubject = forms.CharField(label='Deactivation Email, Subject',
                                         widget=forms.TextInput(attrs={"size":"125"}))

    deactivationText = forms.CharField(label='Deactivation Email, Text',
                                       widget=TinyMCE(attrs={"rows":10, "cols":200, "plugins": "link image code"}))

    passwordResetTextSubject = forms.CharField(label='Password Reset Email, Subject',
                                         widget=forms.TextInput(attrs={"size":"125"}))

    passwordResetText = forms.CharField(label='Password Reset Email, Text',
                                        widget=TinyMCE(attrs={"rows":10, "cols":200, "plugins": "link image code"}))

    emailVerificationTextSubject = forms.CharField(label='Account Creation Verification, Subject',
                                                   widget=forms.TextInput(attrs={"size":"125"}))

    emailVerificationResetText = forms.CharField(label='Account Creation Verification, Text',
                                                 widget=TinyMCE(attrs={"rows":10, "cols":200, "plugins": "link image code"}))
    
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