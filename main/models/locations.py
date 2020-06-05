from django.db import models
import logging
import traceback

#room experiment is run in
class locations(models.Model):
    name = models.CharField(max_length = 300)
    address = models.TextField(null=True)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return self.name
    
    def json(self):
        return{
            "id":self.id,
            "name":self.name,
        }