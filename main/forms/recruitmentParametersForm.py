from django import forms
from main.models import genders,subject_types,institutions,experiments,recruitmentParameters,hrefExperiments
from django.db.models.functions import Lower

class recruitmentParametersForm(forms.ModelForm):   

    actual_participants = forms.CharField(label='Number of Participants', 
                                                  widget=forms.NumberInput(attrs={"v-model":"recruitmentParams.actual_participants",
                                                                                  "v-on:keyup":"recruitmentFormChange",
                                                                                  "v-on:change":"recruitmentFormChange"}))
    registration_cutoff = forms.CharField(label='Registration Cutoff',
                                                  widget=forms.NumberInput(attrs={"v-model":"recruitmentParams.registration_cutoff",
                                                                                  "v-on:keyup":"recruitmentFormChange",
                                                                                  "v-on:change":"recruitmentFormChange"}))  
    gender = forms.ModelMultipleChoiceField(label="Gender(s)", 
                                                    queryset=genders.objects.all(),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"recruitmentParams.gender",
                                                                                        "v-on:change":"recruitmentFormChange",
                                                                                        "class":"selectpicker",
                                                                                        "size":"4"}))                                                               
    subject_type = forms.ModelMultipleChoiceField(label="Subject Type(s)",
                                                    queryset=subject_types.objects.all(),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"recruitmentParams.subject_type",
                                                                                        "v-on:change":"recruitmentFormChange",
                                                                                        "class":"selectpicker",
                                                                                        "size":"4"}))
    institutions_exclude = forms.ModelMultipleChoiceField(label="",
                                                    required=False,
                                                    queryset=institutions.objects.all().order_by(Lower("name")),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"recruitmentParams.institutions_exclude",
                                                                                        "v-on:change":"recruitmentFormChange",
                                                                                        "class":"selectpicker",
                                                                                        "size":"10"}))
    institutions_include = forms.ModelMultipleChoiceField(label="",
                                                    required=False,
                                                    queryset=institutions.objects.all().order_by(Lower("name")),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"recruitmentParams.institutions_include",
                                                                                        "v-on:change":"recruitmentFormChange",
                                                                                        "class":"selectpicker",
                                                                                        "size":"10"}))
    experiments_exclude = forms.ModelMultipleChoiceField(label="",
                                                    required=False,
                                                    queryset=hrefExperiments.objects.all().order_by(Lower("title")),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"recruitmentParams.experiments_exclude",
                                                                                        "v-on:change":"recruitmentFormChange",
                                                                                        "class":"selectpicker",
                                                                                        "size":"12"}))
    experiments_include = forms.ModelMultipleChoiceField(label="",
                                                    required=False,
                                                    queryset=hrefExperiments.objects.all().order_by(Lower("title")),
                                                    widget = forms.CheckboxSelectMultiple(attrs={"v-model":"recruitmentParams.experiments_include",
                                                                                        "v-on:change":"recruitmentFormChange",
                                                                                        "class":"selectpicker",
                                                                                        "size":"12"}))        

    experience_min = forms.CharField(label='Minimum Experiment Experience', 
                                            widget=forms.NumberInput(attrs={"v-model":"recruitmentParams.experience_min",
                                                                            "v-on:keyup":"recruitmentFormChange",
                                                                            "v-on:change":"recruitmentFormChange"}))
    
    experience_max = forms.CharField(label='Maximum Experiment Experience', 
                                            widget=forms.NumberInput(attrs={"v-model":"recruitmentParams.experience_max",
                                                                            "v-on:keyup":"recruitmentFormChange",
                                                                            "v-on:change":"recruitmentFormChange"}))                                                                                                                                                                                                                                                                 

    experience_constraint = forms.TypedChoiceField(label='Enable Experience Constraint?',             
                                         choices=((1, 'Yes'), (0, 'No (faster)')),                
                                         widget=forms.RadioSelect(attrs={"v-model":"recruitmentParams.experience_constraint",
                                                                         "v-on:change":"recruitmentFormChange"}))
    
    institutions_exclude_all = forms.TypedChoiceField(label='', 
                                         choices=((1, 'Exclude if in all.'), (0, 'Exclude if in at least one.')),                   
                                         widget=forms.RadioSelect(attrs={"v-model":"recruitmentParams.institutions_exclude_all",
                                                                         "v-on:change":"recruitmentFormChange"}))

    institutions_include_all = forms.TypedChoiceField(label='',             
                                         choices=((1, 'Include if in all.'), (0,'Include if in at least one.')),                
                                         widget=forms.RadioSelect(attrs={"v-model":"recruitmentParams.institutions_include_all",
                                                                         "v-on:change":"recruitmentFormChange"}))   

    experiments_exclude_all = forms.TypedChoiceField(label='',             
                                         choices=((1, 'Exclude if in all.'), (0, 'Exclude if in at least one.')),                
                                         widget=forms.RadioSelect(attrs={"v-model":"recruitmentParams.experiments_exclude_all",
                                                                         "v-on:change":"recruitmentFormChange"}))   

    experiments_include_all = forms.TypedChoiceField(label='',             
                                         choices=((1, 'Include if in all.'), (0, 'Include if in at least one.')),                
                                         widget=forms.RadioSelect(attrs={"v-model":"recruitmentParams.experiments_include_all",
                                                                         "v-on:change":"recruitmentFormChange"}))

    allow_multiple_participations = forms.TypedChoiceField(label='Allow subjects to participate more than once?',             
                                            choices=((1, 'Yes'), (0, 'No')),                
                                            widget=forms.RadioSelect(attrs={"v-model":"recruitmentParams.allow_multiple_participations",
                                                                            "v-on:change":"recruitmentFormChange"}))

    class Meta:
        model=recruitmentParameters
        #fields = ['id','title', 'experiment_manager', 'actual_participants','registration_cutoff','notes','school','account','department']        
        exclude=[]

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