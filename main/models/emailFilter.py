from django.db import models
import logging
import traceback

#email domain a user must have for recruitment ie @ abc.edu
class emailFilter(models.Model):
    name = models.CharField(max_length = 300)
    domain = models.CharField(max_length = 300)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Email Filter'
        verbose_name_plural = 'Email Filters'
    
    def json(self):
        return{
            "id":self.id,
            "name":self.name,
            "domain":self.domain,
        }