from django import forms

class recruitForm(forms.Form):
    number = forms.CharField(label='How many subjects do you want to add?',
                            widget=forms.NumberInput(attrs={}))
    
    def clean_number(self):
        number = self.data['number']

        try:
            if int(number) <= 0:
                raise forms.ValidationError('Must be greater than zero')       

        except ValueError:
             raise forms.ValidationError('Invalid Entry')
        
        return number