from django import forms
from main.models import faq
from django.contrib.auth.models import User
import pytz


class helpDocForm(forms.ModelForm):


    title = forms.CharField(label='Title',
                            widget=forms.TextInput(attrs={"size":"125"}))
    
    path = forms.CharField(label='URL Path',
                           widget=forms.TextInput(attrs={"size":"125"}))

    text = forms.CharField(label='Text',
                           widget=forms.Textarea(attrs={"rows":"30", "cols":"125"}))


    class Meta:
        model=faq
        fields = ('__all__')