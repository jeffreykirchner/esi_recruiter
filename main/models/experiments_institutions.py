from django.db import models
import logging
import traceback

from . import experiments,institutions

#intermediate table for experiments and institutions
class experiments_institutions(models.Model):
    experiment = models.ForeignKey(experiments,on_delete=models.CASCADE)
    institution = models.ForeignKey(institutions,on_delete=models.CASCADE)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated = models.DateTimeField(auto_now= True)

def __str__(self):
    return "ID: " + self.id

class Meta:
    verbose_name = 'Experiment Institutions'
    verbose_name_plural = 'Experiment Institutions'