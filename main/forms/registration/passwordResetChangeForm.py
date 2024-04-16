from django import forms
from django.contrib.auth.password_validation import validate_password
import logging

#form
class passwordResetChangeForm(forms.Form):

    password1 = forms.CharField(label='New Password',
                               widget=forms.PasswordInput(attrs={"autocomplete":"new-password",
                                                                 "v-model":"password1"}))

    password2 = forms.CharField(label='Repeat New Password',
                                widget=forms.PasswordInput(attrs={"autocomplete":"new-password",
                                                                  "v-model":"password2"}))       


    #check that passwords match
    def clean_password1(self):    
        logger = logging.getLogger(__name__) 
        logger.info("Clean Password1")

        password1 = self.data['password1']

        if password1 != self.data['password2']:
            raise forms.ValidationError('Passwords are not the same')
        
        if validate_password(password1):
            raise forms.ValidationError('Password Error')

        return password1        
