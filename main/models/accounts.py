from django.db import models
import logging
import traceback

from . import departments

#billing account number
class accounts(models.Model):
    name = models.CharField(max_length = 300,default="")
    number = models.CharField(max_length = 100)
    department = models.ForeignKey(departments,on_delete=models.CASCADE)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    class Meta:
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'

    def __str__(self):
        if self.name != "":
            return self.number + "(" + self.name + ")" + " | " + self.department.name
        else:
            return self.number + " | " + self.department.name
    
    def json(self):
        return{
            "str":self.__str__(),
            "id":self.id,
            "name":self.name,
            "number":self.number,
            "department":self.department.json(),
        }