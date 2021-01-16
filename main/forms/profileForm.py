from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from main.models import genders,profile,account_types,majors,subject_types

import logging
import re

#form
class profileForm(forms.Form):
    first_name = forms.CharField(label='First Name', max_length=100)
    last_name = forms.CharField(label='Last Name', max_length=100)
    chapman_id = forms.CharField(label='Student ID (Leave blank if non-student)', max_length=25,required=False)
    email = forms.EmailField(label='Email Address')
    phone = forms.CharField(label = "Phone Number (ex: 5556667777)",max_length = 15)
    gender =  forms.ModelChoiceField(label="To which gender identity do you most identify?",
                                     queryset=genders.objects.all(),
                                     widget=forms.Select(attrs={}))
    major = forms.ModelChoiceField(label="Major (Choose Undeclared if non-student)",
                                     queryset=majors.objects.all().order_by('name'),
                                     widget=forms.Select(attrs={})) 
    subject_type = forms.ModelChoiceField(label="What is your enrollment status?",
                                     queryset=subject_types.objects.all(),
                                     widget=forms.Select(attrs={}))
    studentWorker = forms.ChoiceField(label='Are you a student worker?',             
                                         choices=(('---','---'),('Yes', 'Yes'), ('No', 'No')),
                                         initial='---',                   
                                         widget=forms.Select)                
    password1 = forms.CharField(label='Password',widget=forms.PasswordInput())
    password2 = forms.CharField(label='Repeat Password',widget=forms.PasswordInput())

    def clean_studentWorker(self):
        logger = logging.getLogger(__name__) 
        logger.info("Clean studentWorker")

        studentWorker = self.cleaned_data['studentWorker']

        if studentWorker == "Yes":
            return True
        elif studentWorker == "No":
            return False
        else:
            raise forms.ValidationError("Please answer the question.")

    def clean_phone(self):
        logger = logging.getLogger(__name__) 
        logger.info("Clean Phone")

        phone = self.data['phone']

        if not re.match(r'^\+?1?\d{9,15}$',phone):
            raise forms.ValidationError("Phone number must be entered in the format: '+5556667777'. Up to 15 digits allowed.")

        return phone

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
    
    #check that username/email not already in use
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError(u'Email "%s" is already in use.' % email)
        return email