from tinymce.widgets import TinyMCE

from django import forms

from main.models import FAQ

class HelpDocForm(forms.ModelForm):


    title = forms.CharField(label='Title',
                            widget=forms.TextInput(attrs={"size":"125"}))
    
    path = forms.CharField(label='URL Path',
                           widget=forms.TextInput(attrs={"size":"125"}))

    text = forms.CharField(label='Text',
                           widget=TinyMCE(attrs={"rows":30, "cols":125, "plugins": "link image code"}))

    class Meta:
        model=FAQ
        fields = ('__all__')