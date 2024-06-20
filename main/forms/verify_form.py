from django import forms

class VerifyForm(forms.Form):
    token = forms.CharField()