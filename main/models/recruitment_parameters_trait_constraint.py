from django.db import models
import logging

from main.models import RecruitmentParameters
from main.models import Traits

class RecruitmentParametersTraitConstraint(models.Model):

    trait = models.ForeignKey(Traits,on_delete=models.CASCADE)                                   #trait to that is constrainded
    recruitment_parameter = models.ForeignKey(RecruitmentParameters,
                                              related_name ="trait_constraints",
                                              on_delete=models.CASCADE)                          #recruitment parameter set constraint is attached to

    min_value = models.DecimalField(decimal_places=2, max_digits=10,default = 0)                 #trait value greater than or equal to this
    max_value = models.DecimalField(decimal_places=2, max_digits=10,default = 0)                 #trait value less than or equal to this

    include_if_in_range = models.BooleanField(default=True)                                      #if true include if in range, else exclude in range

    timestamp = models.DateTimeField(auto_now_add= True)
    updated = models.DateTimeField(auto_now= True)   
    
    def __str__(self):
        return "ID: " + str(self.id)

    class Meta:                
        verbose_name = 'Recruitment Trait Constraint'
        verbose_name_plural = 'Recruitment Trait Constraints'

    def setup(self, source):
        '''
        load object from another
        '''
        self.trait = source.trait
        self.recruitment_parameter = source.recruitment_parameter
        self.min_value = source.min_value
        self.max_value = source.max_value
        self.include_if_in_range = source.include_if_in_range

    def json(self):
        mode = "Inc." if self.include_if_in_range else "Exc."

        return{
            "id":self.id,
            "name":f'{self.trait.name} {mode} {self.min_value}-{self.max_value}',
            "trait_name":self.trait.name,
            "trait":self.trait.id,
            "min_value":self.min_value,
            "max_value":self.max_value,
            "recruitment_parameter_id":self.recruitment_parameter.id,
            "include_if_in_range": 1 if self.include_if_in_range else 0,
        }
