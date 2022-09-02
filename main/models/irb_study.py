from pickle import TRUE
from django.db import models


class IrbStudy(models.Model):
    '''
    IRB approved study
    '''
    name = models.CharField(max_length=300, verbose_name="IRB Study Name", unique=True)
    number = models.CharField(max_length=100, verbose_name="IRB Study Number", unique=True)
   
    archived = models.BooleanField(verbose_name="Archived", default=False)                    #if archived hide from useage

    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} - {self.number}'
    
    class Meta:
        verbose_name = 'IRB Study'
        verbose_name_plural = 'IRB Studies'
        ordering=['name']
    
    def json(self):
        return{
            "id":self.id,
            "name":self.name,
            "number":self.number,
        }