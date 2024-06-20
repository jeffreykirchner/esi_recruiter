from tinymce.widgets import TinyMCE

import pytz

from django import forms
from django.contrib.auth.models import User

from main.models import InvitationEmailTemplates

class InvitationEmailTemplateForm(forms.ModelForm):
    '''
    template for experiment invitations
    '''

    name = forms.CharField(label='Name',
                           widget=forms.TextInput(attrs={"size":"125"}))


    # subject_text = forms.CharField(label='Subject',
    #                                      widget=forms.TextInput(attrs={"size":"125"}))

    body_text = forms.CharField(label='Text',
                                widget=TinyMCE(attrs={"rows":"15", 
                                                      "plugins": "link image code",
                                                      "cols":"125"}))

    enabled = forms.BooleanField(label='Visible', required=False, initial=True)

    class Meta:
        model=InvitationEmailTemplates
        fields = ('__all__')