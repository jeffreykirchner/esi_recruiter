from django.db import models

#ESI,ASBE, etc
class departments(models.Model):
    name = models.CharField(max_length=300)
    charge_account = models.CharField(max_length=100)
    petty_cash = models.IntegerField()

    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        ordering=['name']
    
    def json(self):
        return{
            "id":self.id,
            "name":self.name,
        }