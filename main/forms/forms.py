from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from main.models import genders,profile,accountTypes,majors

import logging
import re






    # def clean_blackballed(self):
    #     print(self.cleaned_data['blackballed'])
    #     if self.data['blackballed'] != True and self.data['blackballed'] != False:
    #         raise forms.ValidationError('Please choose True or False.')

    #     return self.data['blackballed']
