from django import forms
from main.models import genders,subject_types,experience_levels,institutions,experiments

class experimentForm2(forms.ModelForm):   

    actual_participants_default = forms.CharField(label='Number of Participants (default)', 
                                                  widget=forms.NumberInput(attrs={"v-model":"experiment.actual_participants_default",
                                                                                  "v-on:keyup":"mainFormChange2",
                                                                                  "v-on:change":"mainFormChange2"}))
    registration_cutoff_default = forms.CharField(label='Registration Cutoff (default)',
                                                  widget=forms.NumberInput(attrs={"v-model":"experiment.registration_cutoff_default",
                                                                                  "v-on:keyup":"mainFormChange2",
                                                                                  "v-on:change":"mainFormChange2"}))  
    gender_default = forms.ModelMultipleChoiceField(label="Gender(s)", 
                                                    queryset=genders.objects.all(),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"experiment.gender_default",
                                                                                        "v-on:change":"mainFormChange2",
                                                                                        "class":"selectpicker",
                                                                                        "size":"4"}))                                                               
    subject_type_default = forms.ModelMultipleChoiceField(label="Subject Type(s)",
                                                    queryset=subject_types.objects.all(),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"experiment.subject_type_default",
                                                                                        "v-on:change":"mainFormChange2",
                                                                                        "class":"selectpicker",
                                                                                        "size":"4"}))
    experience_level_default = forms.ModelChoiceField(label="Experience Level",
                                                    queryset=experience_levels.objects.all(),                                                      
                                                    widget=forms.Select(attrs={"v-model":"experiment.experience_level_default",
                                                                                "v-on:change":"mainFormChange2"}))
    institutions_exclude_default = forms.ModelMultipleChoiceField(label="",
                                                    required=False,
                                                    queryset=institutions.objects.all().order_by("name"),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"experiment.institutions_exclude_default",
                                                                                        "v-on:change":"mainFormChange2",
                                                                                        "class":"selectpicker",
                                                                                        "size":"10"}))
    institutions_include_default = forms.ModelMultipleChoiceField(label="",
                                                    required=False,
                                                    queryset=institutions.objects.all().order_by("name"),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"experiment.institutions_include_default",
                                                                                        "v-on:change":"mainFormChange2",
                                                                                        "class":"selectpicker",
                                                                                        "size":"10"}))
    experiments_exclude_default = forms.ModelMultipleChoiceField(label="",
                                                    required=False,
                                                    queryset=experiments.objects.all().order_by("title"),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"experiment.experiments_exclude_default",
                                                                                        "v-on:change":"mainFormChange2",
                                                                                        "class":"selectpicker",
                                                                                        "size":"12"}))
    experiments_include_default = forms.ModelMultipleChoiceField(label="",
                                                    required=False,
                                                    queryset=experiments.objects.all().order_by("title"),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"experiment.experiments_include_default",
                                                                                        "v-on:change":"mainFormChange2",
                                                                                        "class":"selectpicker",
                                                                                        "size":"12"}))                                                                                                                                                                                                                                                                       

    class Meta:
        model=experiments
        #fields = ['id','title', 'experiment_manager', 'actual_participants','registration_cutoff','notes','school','account','department']        
        exclude=['experiment_manager','title','notes','school','account_default','department_default','institution','length_default']

    def clean_registration_cutoff_default(self):
        registration_cutoff_default = self.data['registration_cutoff_default']
        actual_participants_default = self.data['actual_participants_default']

        try: 
            if int(registration_cutoff_default) <= 0:
                raise forms.ValidationError('Must be greater than zero')                
        
            if int(registration_cutoff_default) < int(actual_participants_default):
                raise forms.ValidationError('Must be greater or equal to than Number of Participants')
        
        except ValueError:
            raise forms.ValidationError('Invalid Entry')

        return registration_cutoff_default

    def clean_actual_participants_default(self):
        actual_participants_default = self.data['actual_participants_default']

        try:
            if int(actual_participants_default) <= 0:
                raise forms.ValidationError('Must be greater than zero')
        except ValueError:
            raise forms.ValidationError('Invalid Entry')

        return actual_participants_default