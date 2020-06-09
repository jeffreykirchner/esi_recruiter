from django import forms

class verifyFormResend(forms.Form):
    email = forms.EmailField(label='Email Address')
    token = forms.CharField()