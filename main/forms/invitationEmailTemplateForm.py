from django import forms
from main.models import Invitation_email_templates
from django.contrib.auth.models import User
import pytz


class InvitationEmailTemplateForm(forms.ModelForm):

    name = forms.CharField(label='Name',
                                         widget=forms.TextInput(attrs={"size":"125"}))


    # subject_text = forms.CharField(label='Subject',
    #                                      widget=forms.TextInput(attrs={"size":"125"}))

    body_text = forms.CharField(label='Text',
                                     widget=forms.Textarea(attrs={"rows":"15", "cols":"125"}))

    enabled = forms.BooleanField(label='Visible',required=False,initial=True)

    class Meta:
        model=Invitation_email_templates
        fields = ('__all__')