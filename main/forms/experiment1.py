from django import forms
from main.models import schools,accounts,institutions,experiments

class experimentForm1(forms.ModelForm):   
    title = forms.CharField(label='Title',
                            widget=forms.TextInput(attrs={"v-model":"experiment.title",
                                                          "v-on:keyup":"mainFormChange1"}))
    experiment_manager = forms.CharField(label='Manager(s)',
                                         widget=forms.TextInput(attrs={"v-model":"experiment.experiment_manager",
                                                                       "v-on:keyup":"mainFormChange1"}))
    actual_participants_default = forms.CharField(label='Number of Participants (default)', 
                                                  widget=forms.NumberInput(attrs={"v-model":"experiment.actual_participants_default",
                                                                                  "v-on:keyup":"mainFormChange1",
                                                                                  "v-on:change":"mainFormChange1"}))
    registration_cutoff_default = forms.CharField(label='Registration Cutoff (default)',
                                                  widget=forms.NumberInput(attrs={"v-model":"experiment.registration_cutoff_default",
                                                                                  "v-on:keyup":"mainFormChange1",
                                                                                  "v-on:change":"mainFormChange1"}))  
    length_default = forms.CharField(label='Length in Minutes (default)',
                                                  widget=forms.NumberInput(attrs={"v-model":"experiment.length_default",
                                                                                  "v-on:keyup":"mainFormChange1",
                                                                                  "v-on:change":"mainFormChange1"}))
    notes = forms.CharField(label='Notes',
                            widget=forms.Textarea(attrs={"v-model":"experiment.notes",
                                                         "v-on:keyup":"mainFormChange1",
                                                         "rows":"12"}),
                            required=False)
    school = forms.ModelChoiceField(queryset=schools.objects.all(),
                                    widget=forms.Select(attrs={"v-model":"experiment.school",
                                                               "v-on:change":"mainFormChange1"}))
    account_default = forms.ModelChoiceField(label="Account (default)",
                                            queryset=accounts.objects.all(),
                                            widget=forms.Select(attrs={"v-model":"experiment.account_default",
                                                                       "v-on:change":"mainFormChange1"}))
    institution = forms.ModelMultipleChoiceField(label="Institution(s)",
                                                 queryset=institutions.objects.all().order_by("name"),
                                                 widget = forms.CheckboxSelectMultiple(attrs={"v-model":"experiment.institution",
                                                                                      "v-on:change":"mainFormChange1",
                                                                                      "class":"selectpicker",
                                                                                      "size":"13"}))                                                                                                                                                                                                                                                                       

    class Meta:
        model=experiments
        #fields = ['id','title', 'experiment_manager', 'actual_participants','registration_cutoff','notes','school','account','department']        
        exclude=['gender_default','subject_type_default','experience_level_default','institutions_exclude_default','institutions_include_default','experiments_exclude_default','experiments_include_default']

    def clean_registration_cutoff_default(self):
        registration_cutoff_default = self.data['registration_cutoff_default']
        actual_participants_default = self.data['actual_participants_default']

        if int(registration_cutoff_default) <= 0:
            raise forms.ValidationError('Must be greater than zero')
        
        if int(registration_cutoff_default) < int(actual_participants_default):
            raise forms.ValidationError('Must be greater or equal to than Number of Participants')
        
        return registration_cutoff_default