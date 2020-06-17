from django import forms
from main.models import genders,subject_types,experience_levels,institutions,experiments,experiment_sessions

class experimentSessionForm1(forms.ModelForm):
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