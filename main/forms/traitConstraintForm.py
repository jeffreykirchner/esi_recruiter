from django import forms
from main.models import Recruitment_parameters_trait_constraint,Traits

import logging

#form
class TraitConstraintForm(forms.ModelForm):

    trait = forms.ModelChoiceField(label="Trait",
                                     queryset=Traits.objects.order_by("name"),
                                     widget=forms.Select(attrs={"v-model":"current_trait.trait_id"}))

    include_if_in_range = forms.ChoiceField(label="Mode",
                                      choices=(('true', "Include if in range."), ('false', "Exclude if in range.")),
                                      widget=forms.Select(attrs={"v-model":"current_trait.include_if_in_range",}))

    min_value = forms.DecimalField(label='Minimum Value',
                              widget=forms.NumberInput(attrs={"v-model":"current_trait.min_value"}))

    max_value = forms.DecimalField(label='Maximum Value',
                              widget=forms.NumberInput(attrs={"v-model":"current_trait.max_value"}))
   
    class Meta:
        model=Recruitment_parameters_trait_constraint
        fields=['trait', 'include_if_in_range', 'min_value', 'max_value']

    
    def clean_include_if_in_range(self):
        '''
        clean include_if_in_range
        '''
        logger = logging.getLogger(__name__)
        logger.info("Clean include_if_in_range")

        val = self.data['include_if_in_range']

        if val == 'true':
            return True

        if val == 'false':
            return False

        raise forms.ValidationError('Invalid Entry')