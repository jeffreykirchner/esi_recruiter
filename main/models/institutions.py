from django.db import models
import logging
import traceback

#type of experiment
class institutions(models.Model):
    name = models.CharField(max_length = 50)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated = models.DateTimeField(auto_now= True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Institution'
        verbose_name_plural = 'Institutions'

    def json(self):
        return{
            "id":self.id,
            "name":self.name,
            }