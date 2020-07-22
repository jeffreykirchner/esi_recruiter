from django import forms
from main.models import genders,subject_types,institutions,experiments

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

    experience_min_default = forms.CharField(label='Minimum Experiment Experience', 
                                            widget=forms.NumberInput(attrs={"v-model":"experiment.experience_min_default",
                                                                            "v-on:keyup":"mainFormChange2",
                                                                            "v-on:change":"mainFormChange2"}))
    
    experience_max_default = forms.CharField(label='Maximum Experiment Experience', 
                                            widget=forms.NumberInput(attrs={"v-model":"experiment.experience_max_default",
                                                                            "v-on:keyup":"mainFormChange2",
                                                                            "v-on:change":"mainFormChange2"}))                                                                                                                                                                                                                                                                 

    experience_constraint_default = forms.TypedChoiceField(label='Enable Experience Constraint?',             
                                         choices=((1, 'Yes'), (0, 'No (faster)')),                
                                         widget=forms.RadioSelect(attrs={"v-model":"experiment.experience_constraint_default",
                                                                         "v-on:change":"mainFormChange2"}))
    
    institutions_exclude_all_default = forms.TypedChoiceField(label='', 
                                         choices=((1, 'Exclude if in all.'), (0, 'Exclude if in at least one.')),                   
                                         widget=forms.RadioSelect(attrs={"v-model":"experiment.institutions_exclude_all_default",
                                                                         "v-on:change":"mainFormChange2"}))

    institutions_include_all_default = forms.TypedChoiceField(label='',             
                                         choices=((1, 'Include if in all.'), (0,'Include if in at least one.')),                
                                         widget=forms.RadioSelect(attrs={"v-model":"experiment.institutions_include_all_default",
                                                                         "v-on:change":"mainFormChange2"}))   

    experiments_exclude_all_default = forms.TypedChoiceField(label='',             
                                         choices=((1, 'Exclude if in all.'), (0, 'Exclude if in at least one.')),                
                                         widget=forms.RadioSelect(attrs={"v-model":"experiment.experiments_exclude_all_default",
                                                                         "v-on:change":"mainFormChange2"}))   

    experiments_include_all_default = forms.TypedChoiceField(label='',             
                                         choices=((1, 'Include if in all.'), (0, 'Include if in at least one.')),                
                                         widget=forms.RadioSelect(attrs={"v-model":"experiment.experiments_include_all_default",
                                                                         "v-on:change":"mainFormChange2"}))

    allow_multiple_participations_default = forms.TypedChoiceField(label='Allow subjects to participate more than once?',             
                                            choices=((1, 'Yes'), (0, 'No')),                
                                            widget=forms.RadioSelect(attrs={"v-model":"experiment.allow_multiple_participations_default",
                                                                            "v-on:change":"mainFormChange2"}))

    class Meta:
        model=experiments
        #fields = ['id','title', 'experiment_manager', 'actual_participants','registration_cutoff','notes','school','account','department']        
        exclude=['experiment_manager','showUpFee','title','notes','school','account_default','department_default','institution','length_default','institutions_exclude_all','institutions_include_all','experiments_exclude_all','experiments_include_all','invitationText']

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
    
    def clean_experience_min_default(self):
        experience_min_default = self.data['experience_min_default']

        try:
            if int(experience_min_default) < 0:
                raise forms.ValidationError('Must be greater than or equal to zero')
        except ValueError:
            raise forms.ValidationError('Invalid Entry')

        return experience_min_default

    def clean_experience_max_default(self):
        experience_max_default = self.data['experience_max_default']
        experience_min_default = self.data['experience_min_default']

        try:
            if int(experience_min_default) > int(experience_max_default):
                raise forms.ValidationError('Must be greater than or equal to Minimum Experience')
        except ValueError:
            raise forms.ValidationError('Invalid Entry')

        return experience_max_default