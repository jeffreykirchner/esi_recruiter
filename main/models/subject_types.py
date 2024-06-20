from django.db import models

class SubjectTypes(models.Model):
    name = models.CharField(verbose_name='Name', max_length=300)
    initialValue = models.BooleanField(verbose_name='Default to On', default=False)    #if true add on initial experiment creation
    display_order = models.IntegerField(verbose_name='Display order', default=1)       #default order in which shown

    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Subject Type'
        verbose_name_plural = 'Subject Types'
        ordering = ['display_order']

    def json(self):
        return{
            "id":self.id,
            "name":self.name,
        }