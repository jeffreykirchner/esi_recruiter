from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import logging
import traceback

#Chapman, etc
class schools(models.Model):
    name = models.CharField(max_length = 300)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return self.name
    
    def json(self):
        return{
            "id":self.id,
            "name":self.name,
        }