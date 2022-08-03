from django.db import models
import logging
import traceback

#list of genders
class genders(models.Model):
    name = models.CharField(verbose_name = 'Name',max_length = 300)                    #name of gender
    initialValue = models.BooleanField(verbose_name = 'Default to On',default=True)    #if true add on initial experiment creation

    timestamp = models.DateTimeField(auto_now_add= True)
    updated = models.DateTimeField(auto_now= True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Gender'
        verbose_name_plural = 'Genders'

    def json(self):
        return{
            "id":self.id,
            "name":self.name,
        }