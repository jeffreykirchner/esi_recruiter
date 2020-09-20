from django.db import models
import logging
import traceback
from . import email_filters

#Chapman, etc
class schools(models.Model):
    name = models.CharField(max_length = 300, verbose_name = 'Name')
    email_filter = models.ManyToManyField(email_filters,blank=True, verbose_name = 'Email Filters')     

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'School'
        verbose_name_plural = 'Schools'
    
    def json(self):
        return{
            "id":self.id,
            "name":self.name,
        }