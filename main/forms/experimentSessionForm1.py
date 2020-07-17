from django import forms
from main.models import genders,subject_types,institutions,experiments,experiment_sessions,hrefExperiments

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
                                                    queryset=hrefExperiments.objects.all().order_by("title"),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"session.experiments_exclude",
                                                                                        "v-on:change":"mainFormChange1",
                                                                                        "class":"selectpicker",
                                                                                        "size":"10"}))
    experiments_include = forms.ModelMultipleChoiceField(label="",
                                                    required=False,
                                                    queryset=hrefExperiments.objects.all().order_by("title"),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"session.experiments_include",
                                                                                        "v-on:change":"mainFormChange1",
                                                                                        "class":"selectpicker",
                                                                                        "size":"10"}))  
    
    experience_min = forms.CharField(label='Minimum Experiment Experience', 
                                            widget=forms.NumberInput(attrs={"v-model":"session.experience_min",
                                                                            "v-on:keyup":"mainFormChange1",
                                                                            "v-on:change":"mainFormChange1"}))
    
    experience_max = forms.CharField(label='Maximum Experiment Experience', 
                                            widget=forms.NumberInput(attrs={"v-model":"session.experience_max",
                                                                            "v-on:keyup":"mainFormChange1",
                                                                            "v-on:change":"mainFormChange1"}))

    experience_constraint = forms.TypedChoiceField(label='Enable Experience Constraint?',             
                                         choices=((1, 'Yes'), (0, 'No (faster)')),                
                                         widget=forms.RadioSelect(attrs={"v-model":"session.experience_constraint",
                                                                         "v-on:change":"mainFormChange1"}))
    
    institutions_exclude_all = forms.TypedChoiceField(label='', 
                                         choices=((1, 'Exclude if in all.'), (0, 'Exclude if in at least one.')),                   
                                         widget=forms.RadioSelect(attrs={"v-model":"session.institutions_exclude_all",
                                                                         "v-on:change":"mainFormChange1"}))

    institutions_include_all = forms.TypedChoiceField(label='',             
                                         choices=((1, 'Include if in all.'), (0,'Include if in at least one.')),                
                                         widget=forms.RadioSelect(attrs={"v-model":"session.institutions_include_all",
                                                                         "v-on:change":"mainFormChange1"}))   

    experiments_exclude_all = forms.TypedChoiceField(label='',             
                                         choices=((1, 'Exclude if in all.'), (0, 'Exclude if in at least one.')),                
                                         widget=forms.RadioSelect(attrs={"v-model":"session.experiments_exclude_all",
                                                                         "v-on:change":"mainFormChange1"}))   

    experiments_include_all = forms.TypedChoiceField(label='',             
                                         choices=((1, 'Include if in all.'), (0, 'Include if in at least one.')),                
                                         widget=forms.RadioSelect(attrs={"v-model":"session.experiments_include_all",
                                                                         "v-on:change":"mainFormChange1"}))

    allow_multiple_participations = forms.TypedChoiceField(label='Allow subjects to participate more than once?',             
                                         choices=((1, 'Yes'), (0, 'No')),                
                                         widget=forms.RadioSelect(attrs={"v-model":"session.allow_multiple_participations",
                                                                         "v-on:change":"mainFormChange1"}))

    class Meta:
        model = experiment_sessions
        exclude=['experiment','showUpFee_legacy']

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
    
    def clean_experience_min(self):
        experience_min = self.data['experience_min']

        try:
            if int(experience_min) < 0:
                raise forms.ValidationError('Must be greater than or equal to zero')
        except ValueError:
            raise forms.ValidationError('Invalid Entry')

        return experience_min

    def clean_experience_max(self):
        experience_max = self.data['experience_max']
        experience_min = self.data['experience_min']

        try:
            if int(experience_min) > int(experience_max):
                raise forms.ValidationError('Must be greater than or equal to Minimum Experience')
        except ValueError:
            raise forms.ValidationError('Invalid Entry')

        return experience_max