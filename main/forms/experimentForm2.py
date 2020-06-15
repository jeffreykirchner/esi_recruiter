from django import forms
from main.models import genders,subject_types,experience_levels,institutions,experiments

class experimentForm2(forms.ModelForm):   
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
        exclude=['title','experiment_manager','actual_participants_default','registration_cutoff_default','notes','school','account_default','department_default','institution','length_default']
