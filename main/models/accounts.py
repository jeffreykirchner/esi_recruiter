from django.db import models

from . import departments

#billing account number
class accounts(models.Model):
    name = models.CharField(max_length = 300,default="")
    number = models.CharField(max_length = 100)
    department = models.ForeignKey(departments, on_delete=models.CASCADE)

    archived = models.BooleanField(verbose_name="Archived", default=False)                    #if archived hide from useage
    outside_funding = models.BooleanField(verbose_name="Outside Funding", default=False)      #payments are coming from outside the oganization

    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
        ordering = ['department__name', 'number']

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
            "archived":self.archived,
            "outside_funding":self.outside_funding,
        }