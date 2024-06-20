from tinymce.widgets import TinyMCE

from django import forms

from main.models import FrontPageNotice

class FrontPageNoticeForm(forms.ModelForm):


    subject_text = forms.CharField(label='Subject Text',
                                         widget=forms.TextInput(attrs={"size":"125"}))
    
    body_text = forms.CharField(label='Body Text',
                                widget=TinyMCE(attrs={"rows":30, "cols":125, "plugins": "link image code"}))

    enabled = forms.BooleanField(label='Activate',required=False)


    class Meta:
        model=FrontPageNotice
        fields = ('__all__')