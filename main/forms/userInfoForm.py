from django import forms
from main.models import genders,profile,account_types,majors

class userInfoForm(forms.Form):
    class Meta:
        model=profile
        exclude=['labUser','email_confirmed','user']

    first_name = forms.CharField(label='First Name',
                                 widget=forms.TextInput(attrs={"v-on:change":"userChange"}))
    
    last_name = forms.CharField(label='Last Name',
                                widget=forms.TextInput(attrs={"v-on:change":"userChange"}))

    email = forms.EmailField(label='Email Address',
                                widget=forms.TextInput(attrs={"v-on:change":"userChange"}))

    studentID = forms.CharField(label='Student ID (Leave blank if non-student)',
                                required=False,
                                widget=forms.TextInput(attrs={"v-on:change":"userChange"}))

    type = forms.ModelChoiceField(label = "Account Type",
                                         queryset=account_types.objects.all(),
                                         widget=forms.Select(attrs={"v-on:change":"userChange"}))

    gender = forms.ModelChoiceField(label = "Gender",
                                         queryset=genders.objects.all(),
                                         widget=forms.Select(attrs={"v-on:change":"userChange"}))
                                        
    blackballed = forms.TypedChoiceField(label='Blackballed',             
                                        #  coerce=lambda x: bool(int(x)),
                                         choices=((False, 'true'), (True, 'false')),                   
                                         widget=forms.RadioSelect(attrs={"v-on:change":"userChange"}))