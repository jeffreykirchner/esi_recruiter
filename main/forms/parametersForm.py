from django import forms
from main.models import parameters
from django.contrib.auth.models import User
from django.forms import ModelChoiceField

class UserModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
         return obj.get_full_name()

class parametersForm(forms.ModelForm):
    labManager = UserModelChoiceField(label="Lab Manager",
                                     queryset=User.objects.filter(is_staff = True).order_by('last_name','first_name'),
                                     widget=forms.Select(attrs={})) 

    invitationText = forms.CharField(label='Default Recruitment Email',
                                     widget=forms.Textarea(attrs={"rows":"10", "cols":"125"}))
    
    consentForm = forms.CharField(label='Consent Form',
                                     widget=forms.Textarea(attrs={"rows":"25", "cols":"125"}))
    
    class Meta:
        model=parameters
        fields = ('__all__')