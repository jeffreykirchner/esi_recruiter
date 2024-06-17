'''
update profile form
'''
import logging
import re

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from main.models import Genders, Majors, subject_types

class profileFormUpdate(forms.Form):
    '''
    update profile form
    '''
    first_name = forms.CharField(label='First Name',
                                 max_length=100,
                                 widget=forms.TextInput(attrs={"v-model":"profile.first_name"}))
    
    last_name = forms.CharField(label='Last Name',
                                max_length=100,
                                widget=forms.TextInput(attrs={"v-model":"profile.last_name"}))
    
    chapman_id = forms.CharField(label='Student ID (Leave blank if non-student)',
                                 max_length=25,
                                 required=False,
                                 widget=forms.TextInput(attrs={"v-model":"profile.chapman_id"}))
      
    email = forms.EmailField(label='Email Address (Verification required.)',
                             widget=forms.TextInput(attrs={"autocomplete":"off",
                                                           "v-model":"profile.email"}))
    
    phone = forms.CharField(label = "Phone Number (ex: 5556667777)",
                            max_length = 15,
                            widget=forms.TextInput(attrs={"v-model":"profile.phone"}))
    
    gender =  forms.ModelChoiceField(label="To which gender identity do you most identify?",
                                     queryset=Genders.objects.all(),
                                     empty_label=None,
                                     widget=forms.Select(attrs={"v-model":"profile.gender"}))
    
    major = forms.ModelChoiceField(label="Major (Choose Undeclared if non-student)",
                                   queryset=Majors.objects.all().order_by('name'),
                                   empty_label=None,
                                   widget=forms.Select(attrs={"v-model":"profile.major"}))
    
    subject_type = forms.ModelChoiceField(label="What is your enrollment status?",
                                          queryset=subject_types.objects.all(),
                                          empty_label=None,
                                          widget=forms.Select(attrs={"v-model":"profile.subject_type"}))
    
    studentWorker = forms.ChoiceField(label='Are you a student worker?',             
                                      choices=((1, 'Yes'), (0, 'No')),                                                          
                                      widget=forms.Select(attrs={"v-model":"profile.studentWorker"}))
    
    paused = forms.ChoiceField(label='Pause your account?  You will not receive invitations while paused.',             
                               choices=((1, 'Yes'), (0, 'No')),                                                          
                               widget=forms.Select(attrs={"v-model":"profile.paused"}))
    
    password1 = forms.CharField(label='Password (Leave blank for no change.)',
                                widget=forms.PasswordInput(attrs={"autocomplete":"new-password",
                                                                  "v-model":"profile.password1"}),
                                required=False)
    
    password2 = forms.CharField(label='Repeat Password',
                                widget=forms.PasswordInput(attrs={"autocomplete":"new-password",
                                                                  "v-model":"profile.password2"}),
                                required=False)

    # def clean_studentWorker(self):
    #     logger = logging.getLogger(__name__) 
    #     logger.info("Clean studentWorker")

    #     studentWorker = self.cleaned_data['studentWorker']

    #     if studentWorker == "Yes":
    #         return True
    #     elif studentWorker == "No":
    #         return False
    #     else:
    #         raise forms.ValidationError("Please answer the question.")
    
    # def clean_paused(self):
    #     logger = logging.getLogger(__name__) 
    #     logger.info("Clean paused")

    #     paused = self.cleaned_data['paused']

    #     if paused == "Yes":
    #         return True
    #     elif paused == "No":
    #         return False
    #     else:
    #         raise forms.ValidationError("Please answer the question.")

    def clean_phone(self):
        logger = logging.getLogger(__name__) 
        logger.info("Clean Phone")

        phone = self.data['phone']

        if not re.match(r'^\+?1?\d{9,15}$',phone):
            raise forms.ValidationError("Phone number must be entered in the format: '+5556667777'. Up to 15 digits allowed.")

        return phone

    def __init__(self, *args, **kwargs):
         self.user = kwargs.pop('user', None)
         super(profileFormUpdate, self).__init__(*args, **kwargs)

    #check that passwords match
    def clean_password1(self):
        if self.data['password1'] != "":        
            password1 = self.data['password1']

            if password1 != self.data['password2']:
                raise forms.ValidationError('Passwords are not the same')
            
            if validate_password(password1):
                raise forms.ValidationError('Password Error')

            return password1
        else:
            return ""

     #check that username/email not already in use
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(username=email).exclude(id=self.user.id).exists():
            raise forms.ValidationError(u'Email "%s" is already in use.' % email)
        return email

