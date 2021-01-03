from django import forms

import logging

#form
class passwordResetForm(forms.Form):

    username =  forms.EmailField(label='Email address (lower case)',
                                 widget=forms.TextInput(attrs={}) )      
