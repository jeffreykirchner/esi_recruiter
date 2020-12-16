from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from main.models import Traits

import logging
import re

#form
class traitReportForm(forms.Form):
    traits = forms.ModelMultipleChoiceField(label="Traits",
                                                 queryset=Traits.objects.all().order_by("name"),
                                                 widget = forms.CheckboxSelectMultiple(attrs={}))


    