import logging

from django import forms
from django.db.models.functions import Lower

from main.models import Traits
from main.models import HrefTraits

# trait report form
class TraitReportForm(forms.Form):
    traits = forms.ModelMultipleChoiceField(label="",
                                            required=False,
                                            queryset=HrefTraits.objects.filter(archived=False),
                                            widget = forms.CheckboxSelectMultiple(attrs={"v-model":"selected_traits"}))


    