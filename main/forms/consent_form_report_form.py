import logging

from django import forms

from main.models import ConsentForm

#form
class ConsentFormReportForm(forms.Form):

    consent_form =  forms.ModelChoiceField(label="Consent Form",
                                           required=True,
                                           empty_label=None,
                                           queryset=ConsentForm.objects.all(),
                                           widget=forms.Select(attrs={"v-model":"consent_form_choice"}))
               