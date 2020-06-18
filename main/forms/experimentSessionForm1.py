from django import forms
from main.models import genders,subject_types,experience_levels,institutions,experiments,experiment_sessions

class experimentSessionForm1(forms.ModelForm):
    actual_participants = forms.CharField(label='Number of Participants', 
                                            widget=forms.NumberInput(attrs={"v-model":"session.actual_participants",
                                                                            "v-on:keyup":"mainFormChange1",
                                                                            "v-on:change":"mainFormChange1"}))

    registration_cutoff = forms.CharField(label='Registration Cutoff',
                                            widget=forms.NumberInput(attrs={"v-model":"session.registration_cutoff",
                                                                            "v-on:keyup":"mainFormChange1",
                                                                            "v-on:change":"mainFormChange1"}))
    gender = forms.ModelMultipleChoiceField(label="Gender(s)", 
                                                queryset=genders.objects.all(),
                                                widget = forms.CheckboxSelectMultiple(attrs={"v-model":"session.gender",
                                                                                    "v-on:change":"mainFormChange1",
                                                                                    "class":"selectpicker",
                                                                                    "size":"4"}))                                                               
    subject_type = forms.ModelMultipleChoiceField(label="Subject Type(s)",
                                                    queryset=subject_types.objects.all(),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"session.subject_type",
                                                                                        "v-on:change":"mainFormChange1",
                                                                                        "class":"selectpicker",
                                                                                        "size":"4"}))
    experience_level = forms.ModelChoiceField(label="Experience Level",
                                                    queryset=experience_levels.objects.all(),                                                      
                                                    widget=forms.Select(attrs={"v-model":"session.experience_level",
                                                                                "v-on:change":"mainFormChange1"}))
    institutions_exclude = forms.ModelMultipleChoiceField(label="",
                                                    required=False,
                                                    queryset=institutions.objects.all().order_by("name"),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"session.institutions_exclude",
                                                                                        "v-on:change":"mainFormChange1",
                                                                                        "class":"selectpicker",
                                                                                        "size":"10"}))
    institutions_include = forms.ModelMultipleChoiceField(label="",
                                                    required=False,
                                                    queryset=institutions.objects.all().order_by("name"),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"session.institutions_include",
                                                                                        "v-on:change":"mainFormChange1",
                                                                                        "class":"selectpicker",
                                                                                        "size":"10"}))
    experiments_exclude = forms.ModelMultipleChoiceField(label="",
                                                    required=False,
                                                    queryset=experiments.objects.all().order_by("title"),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"session.experiments_exclude",
                                                                                        "v-on:change":"mainFormChange1",
                                                                                        "class":"selectpicker",
                                                                                        "size":"10"}))
    experiments_include = forms.ModelMultipleChoiceField(label="",
                                                    required=False,
                                                    queryset=experiments.objects.all().order_by("title"),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"session.experiments_include",
                                                                                        "v-on:change":"mainFormChange1",
                                                                                        "class":"selectpicker",
                                                                                        "size":"10"}))  

    class Meta:
        model = experiment_sessions
        exclude=['experiment']

    def clean_registration_cutoff(self):
        registration_cutoff = self.data['registration_cutoff']
        actual_participants = self.data['actual_participants']

        try:
            if int(registration_cutoff) <= 0:
                raise forms.ValidationError('Must be greater than zero')       
        
            if int(registration_cutoff) < int(actual_participants):
                raise forms.ValidationError('Must be greater or equal to than Number of Participants')

        except ValueError:
             raise forms.ValidationError('Invalid Entry')
        
        return registration_cutoff

    def clean_actual_participants(self):
        actual_participants = self.data['actual_participants']

        try:
            if int(actual_participants) <= 0:
                raise forms.ValidationError('Must be greater than zero')
        
        except ValueError:
             raise forms.ValidationError('Invalid Entry')

        return actual_participants