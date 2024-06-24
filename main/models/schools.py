import logging
import traceback

from django.db import models

from main.models import EmailFilters

#Chapman, etc
class Schools(models.Model):
    name = models.CharField(max_length=300, verbose_name='Name')
    email_filter = models.ManyToManyField(EmailFilters, blank=True, verbose_name='Email Filters')      #email domains that determine if in school
    initialValue = models.BooleanField(verbose_name='Default to On', default=False)                     #if true add on initial experiment creation

    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

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