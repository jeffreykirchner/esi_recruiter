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
    
    consentForm = forms.CharField(label='Consent Form',
                                     widget=forms.Textarea(attrs={"rows":"25", "cols":"125"}))

    subjectTimeZone = forms.ChoiceField(label="Subject Timezone",
                                        choices=[(tz, tz) for tz in pytz.all_timezones])
    
    class Meta:
        model=parameters
        fields = ('__all__')