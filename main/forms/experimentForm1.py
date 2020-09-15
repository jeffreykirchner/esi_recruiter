from django import forms
from main.models import schools,accounts,institutions,experiments

class experimentForm1(forms.ModelForm):   
    title = forms.CharField(label='Title',
                            widget=forms.TextInput(attrs={"v-model":"experiment.title",
                                                          "v-on:keyup":"mainFormChange1"}))
    experiment_manager = forms.CharField(label='Manager(s)',
                                         widget=forms.TextInput(attrs={"v-model":"experiment.experiment_manager",
                                                                       "v-on:keyup":"mainFormChange1"}))

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

    showUpFee = forms.CharField(label='Show-up Fee ($)', 
                                            widget=forms.NumberInput(attrs={"v-model":"experiment.showUpFee",
                                                                            "v-on:keyup":"mainFormChange1",
                                                                            "v-on:change":"mainFormChange1"}))

    institution = forms.ModelMultipleChoiceField(label="",
                                                 queryset=institutions.objects.all().order_by("name"),
                                                 widget = forms.CheckboxSelectMultiple(attrs={"v-model":"experiment.institution",
                                                                                      "v-on:change":"mainFormChange1",
                                                                                      "class":"selectpicker",
                                                                                      "size":"13",
                                                                                      "v-bind:disabled":"experiment.confirmationFound === true"}))    

    invitationText = forms.CharField(label='Recruitment Email',
                                     widget=forms.Textarea(attrs={"v-model":"experiment.invitationText",
                                                                  "v-on:keyup":"mainFormChange1",
                                                                  "rows":"12"}))                                                                                                                                                                                                                                                                   

    class Meta:
        model=experiments
        #fields = ['id','title', 'experiment_manager', 'actual_participants','registration_cutoff','notes','school','account','department']        
        exclude=['actual_participants_legacy','registration_cutoff_legacy','recruitmentParamsDefault']

    def clean_length_default(self):
        length_default = self.data['length_default']

        try:
            if int(length_default) < 0:
                raise forms.ValidationError('Must be greater than zero')
        except ValueError:
            raise forms.ValidationError('Invalid Entry')

        return length_default