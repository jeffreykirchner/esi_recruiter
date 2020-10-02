from django import forms
from main.models import faq
from django.contrib.auth.models import User
import pytz


class faqForm(forms.ModelForm):


    question = forms.CharField(label='Question',
                                         widget=forms.TextInput(attrs={"size":"125"}))

    answer = forms.CharField(label='Answer',
                                     widget=forms.Textarea(attrs={"rows":"15", "cols":"125"}))

    active = forms.TypedChoiceField(label='Show Question', 
                                         choices=((True, 'Yes'), (False, 'No')),                   
                                         widget=forms.RadioSelect(attrs={}))

    
    order = forms.CharField(label='Order in which questions appear',
                                       widget=forms.NumberInput(attrs={}))

    class Meta:
        model=faq
        fields = ('__all__')