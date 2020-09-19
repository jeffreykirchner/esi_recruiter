from django.db import models
import logging
import traceback

#subject, staff
class account_types(models.Model):
    name = models.CharField(max_length = 300)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return self.name.upper()
    
    class Meta:
        verbose_name = 'Account Type'
        verbose_name_plural = 'Account Types'

    def json(self):
        return{
            "id":self.id,
            "name":self.name,
        }