from django import forms
from main.models import Front_page_notice
from django.contrib.auth.models import User
import pytz


class frontPageNoticeForm(forms.ModelForm):


    subject_text = forms.CharField(label='Subject Text',
                                         widget=forms.TextInput(attrs={"size":"125"}))
    
    body_text = forms.CharField(label='Body Text',
                                         widget=forms.Textarea(attrs={"rows":"30", "cols":"125"}))

    enabled = forms.BooleanField(label='Activate',required=False)


    class Meta:
        model=Front_page_notice
        fields = ('__all__')