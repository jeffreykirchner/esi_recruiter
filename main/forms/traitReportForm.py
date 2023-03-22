import logging

from django import forms
from django.db.models.functions import Lower

from main.models import Traits
from main.models import HrefTraits

# trait report form
class traitReportForm(forms.Form):
    traits = forms.ModelMultipleChoiceField(label="",
                                            queryset=HrefTraits.objects.filter(archived=False),
                                            widget = forms.CheckboxSelectMultiple(attrs={}))


    