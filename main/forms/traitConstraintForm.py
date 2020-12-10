from django import forms
from main.models import Recruitment_parameters_trait_constraint,Traits

import logging

#form
class TraitConstraintForm(forms.ModelForm):

    trait = forms.ModelChoiceField(label="Trait",
                                     queryset=Traits.objects.filter(),
                                     widget=forms.Select(attrs={"v-model":"current_trait.trait_id"}))

    min_value = forms.DecimalField(label='Minimum Allowed Value',
                              widget=forms.NumberInput(attrs={"v-model":"current_trait.min_value"}))

    max_value = forms.DecimalField(label='Maximum Allowed Value',
                              widget=forms.NumberInput(attrs={"v-model":"current_trait.max_value"}))

    class Meta:
        model=Recruitment_parameters_trait_constraint
        exclude=['recruitment_parameter']