from django.db import models


# list of sexes
class Sexes(models.Model):
    name = models.CharField(verbose_name='Name', max_length=300)  # name of sex
    initialValue = models.BooleanField(verbose_name='Default to On', default=True)  # if true add on initial experiment creation

    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Sex'
        verbose_name_plural = 'Sexes'

    def json(self):
        return {
            "id": self.id,
            "name": self.name,
        }
