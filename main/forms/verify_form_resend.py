from django import forms

class VerifyFormResend(forms.Form):
    email = forms.EmailField(label='Email Address')
    token = forms.CharField()