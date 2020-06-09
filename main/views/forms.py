from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from main.models import genders,profile,accountTypes,majors

import logging
import re

#form
class profileForm(forms.Form):
    first_name = forms.CharField(label='First Name', max_length=100)
    last_name = forms.CharField(label='Last Name', max_length=100)
    chapman_id = forms.CharField(label='Chapman ID', max_length=25)
    email = forms.EmailField(label='Email Address')
    phone = forms.CharField(label = "Phone Number (ex: 5556667777)",max_length = 15)
    gender =  forms.ModelChoiceField(label="To which gender identity do you most identify?",
                                     queryset=genders.objects.all(),
                                     widget=forms.Select(attrs={"v-model":"profile.gender"}))
    major = forms.ModelChoiceField(label="Major",
                                     queryset=majors.objects.all().order_by('name'),
                                     widget=forms.Select(attrs={"v-model":"profile.major"})) 
    gradStudent = forms.ChoiceField(label='Are you in a Masters, Law or Doctoral program?',             
                                         choices=(('---','---'),('Yes', 'Yes'), ('No', 'No')),
                                         initial='---',                   
                                         widget=forms.Select)
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

    def clean_gradStudent(self):
        logger = logging.getLogger(__name__) 
        logger.info("Clean gradStudent")

        gradStudent = self.cleaned_data['gradStudent']

        if gradStudent == "Yes":
            return True
        elif gradStudent == "No":
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


class profileFormUpdate(forms.Form):
    first_name = forms.CharField(label='First Name', max_length=100)
    last_name = forms.CharField(label='Last Name', max_length=100)
    chapman_id = forms.CharField(label='Chapman ID', max_length=25,required=False)  
    email = forms.EmailField(label='Email Address (Verification required.)')
    gender =  forms.ModelChoiceField(label="To which gender identity do you most identify?",
                                     queryset=genders.objects.all(),
                                     widget=forms.Select(attrs={"v-model":"profile.gender"}))  
    password1 = forms.CharField(label='Password (Leave blank for no change.)',widget=forms.PasswordInput(),required=False)
    password2 = forms.CharField(label='Repeat Password',widget=forms.PasswordInput(),required=False)

    def __init__(self, *args, **kwargs):
         self.user = kwargs.pop('user',None)
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
        if User.objects.filter(username=email).exclude(id = self.user.id).exists():
            raise forms.ValidationError(u'Email "%s" is already in use.' % email)
        return email

class verifyForm(forms.Form):
    token = forms.CharField()

class verifyFormResend(forms.Form):
    email = forms.EmailField(label='Email Address')
    token = forms.CharField()

class userInfoForm(forms.Form):
    class Meta:
        model=profile
        exclude=['labUser','emailConfirmed','user']

    first_name = forms.CharField(label='First Name',
                                 widget=forms.TextInput(attrs={"v-on:change":"userChange"}))
    
    last_name = forms.CharField(label='Last Name',
                                widget=forms.TextInput(attrs={"v-on:change":"userChange"}))

    email = forms.EmailField(label='Email Address',
                                widget=forms.TextInput(attrs={"v-on:change":"userChange"}))

    chapmanID = forms.CharField(label='Chapman ID',
                                required=False,
                                widget=forms.TextInput(attrs={"v-on:change":"userChange"}))

    type = forms.ModelChoiceField(label = "Account Type",
                                         queryset=accountTypes.objects.all(),
                                         widget=forms.Select(attrs={"v-on:change":"userChange"}))

    gender = forms.ModelChoiceField(label = "Gender",
                                         queryset=genders.objects.all(),
                                         widget=forms.Select(attrs={"v-on:change":"userChange"}))
                                        
    blackballed = forms.TypedChoiceField(label='Blackballed',             
                                        #  coerce=lambda x: bool(int(x)),
                                         choices=((False, 'true'), (True, 'false')),                   
                                         widget=forms.RadioSelect(attrs={"v-on:change":"userChange"}))

    # def clean_blackballed(self):
    #     print(self.cleaned_data['blackballed'])
    #     if self.data['blackballed'] != True and self.data['blackballed'] != False:
    #         raise forms.ValidationError('Please choose True or False.')

    #     return self.data['blackballed']
