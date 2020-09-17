from django.db import models
import logging
import traceback

class subject_types(models.Model):
    name = models.CharField(verbose_name = 'Name',max_length = 300)
    initialValue = models.BooleanField(verbose_name = 'Default to On',default=False)    #if true add on initial experiment creation

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Subject Type'
        verbose_name_plural = 'Subject Types'

    def json(self):
        return{
            "id":self.id,
            "name":self.name,
        }