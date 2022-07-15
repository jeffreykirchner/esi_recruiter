
from django.db import models
from django.db.models.functions import Lower

class Traits(models.Model): 
    name = models.CharField(verbose_name='Name', max_length=300, unique=True)      #unique name of trait
    description = models.CharField(verbose_name='Description', max_length=300)     #description of trait
    archived =  models.BooleanField(verbose_name="Archived", default=False)        #if archived hide from useage

    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Trait'
        verbose_name_plural = 'Traits'
        ordering = [Lower('name')]

    def json(self):
        return{
            "id":self.id,
            "name":self.name,
            "description":self.description,
            "archived":self.archived,
        }