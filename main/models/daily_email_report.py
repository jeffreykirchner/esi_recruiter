from django.db import models

#frequently asked questions
class DailyEmailReport(models.Model):
    '''
    report about the previous days activity
    '''
    text = models.CharField(verbose_name="Text", max_length = 100000)            #the text of the report
    date = models.DateField(auto_now_add= True)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return str(self.date.strftime("%#m/%#d/%Y"))
    
    class Meta:
        verbose_name = 'Daily Email Report'
        verbose_name_plural = 'Daily Email Report'
        ordering = ['timestamp']
    
    def json(self):
        return{
            "text" : self.id,
            "date" : self.timestamp,
        }