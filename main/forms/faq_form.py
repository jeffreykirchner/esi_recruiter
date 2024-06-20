from tinymce.widgets import TinyMCE

from django import forms
from main.models import FAQ

class FaqForm(forms.ModelForm):

    question = forms.CharField(label='Question',
                                         widget=forms.TextInput(attrs={"size":"125"}))

    answer = forms.CharField(label='Answer',
                             widget=TinyMCE(attrs={"rows":"12"}))

    active = forms.TypedChoiceField(label='Show Question', 
                                    choices=((True, 'Yes'), (False, 'No')),                   
                                    widget=forms.RadioSelect(attrs={}))

    
    order = forms.CharField(label='Order in which questions appear',
                                       widget=forms.NumberInput(attrs={}))

    class Meta:
        model=FAQ
        fields = ('__all__')