from django.db import models
import logging
import traceback

#desired level of subject experience , none, one or more, any
class experience_levels(models.Model):
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