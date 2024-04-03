from tinymce.models import HTMLField

from django.db import models
from django.utils.safestring import mark_safe

#frequently asked questions
class faq(models.Model):
    question = models.CharField(verbose_name="Question", max_length = 300)              #the question
    answer= HTMLField(verbose_name="Answer", max_length = 10000)                        #the answer to the question
    active = models.BooleanField(verbose_name="Show Question", default=True)            #hide question if false
    order = models.IntegerField(verbose_name="Display Order", default=1)                #order in which the questions will be shown 

    timestamp = models.DateTimeField(auto_now_add= True)
    updated = models.DateTimeField(auto_now= True)

    def __str__(self):
        return self.question
    
    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['order']
    
    def json(self):
        return{
            "id":self.id,
            "question":mark_safe(self.question),
            "answer":mark_safe(self.answer),
            "active":self.active,
            "order":self.order,
        }