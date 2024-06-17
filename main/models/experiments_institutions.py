from django.db import models
import logging
import traceback

from main.models import Experiments
from main.models import Institutions

#intermediate table for experiments and institutions
class ExperimentsInstitutions(models.Model):
    experiment = models.ForeignKey(Experiments,on_delete=models.CASCADE)
    institution = models.ForeignKey(Institutions,on_delete=models.CASCADE)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated = models.DateTimeField(auto_now= True)

def __str__(self):
    return "ID: " + self.id

class Meta:
    verbose_name = 'Experiment Institutions'
    verbose_name_plural = 'Experiment Institutions'