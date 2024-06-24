from django import forms
from main.models import InvitationEmailTemplates

class InvitationEmailTemplateSelectForm(forms.Form):   
    
    invitation_email_template = forms.ModelChoiceField(label="Invitation Email Templates",
                                                     queryset=InvitationEmailTemplates.objects.filter(enabled=True)
                                                                                                  .order_by('name'),
                                                        blank=False,
                                                        empty_label=None,
                                                        required=False,
                                                        widget=forms.Select(attrs={"v-model":"invitation_email_template"}))
                                                                                                                                                                                                                                                                 
