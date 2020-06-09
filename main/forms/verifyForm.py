from django import forms

class verifyForm(forms.Form):
    token = forms.CharField()