from django import forms
from django.contrib.auth.models import User
from django.forms import ModelChoiceField

from main.models import profile
from main.models import Departments

class UserModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
         return f'{obj.user.last_name}, {obj.user.first_name}'

class ExpenditureReportForm(forms.Form):
    
    department = forms.ModelChoiceField(label="Department",
                                           required=False,
                                           empty_label="All Departments",
                                           queryset=Departments.objects.all(),
                                           widget=forms.Select(attrs={"v-model":"expenditure_report.department"}))

    budget = UserModelChoiceField(label="Budget",
                                  required=False,
                                  empty_label="All Budgets",
                                  queryset=profile.objects.filter(type=1)
                                                          .filter(user__is_active=True)
                                                          .order_by('user__last_name','user__first_name'),
                                  widget=forms.Select(attrs={"v-model":"expenditure_report.budget"}))
