from django.db import models
import logging

from . import recruitment_parameters,Traits

class Recruitment_parameters_trait_constraint(models.Model):

    trait = models.ForeignKey(Traits,on_delete=models.CASCADE)                                   #trait to that is constrainded
    recruitment_parameter = models.ForeignKey(recruitment_parameters,
                                              related_name ="trait_constraints",
                                              on_delete=models.CASCADE)                          #recruitment parameter set constraint is attached to

    min_value = models.DecimalField(decimal_places=2, max_digits=10,default = 0)                 #trait value greater than or equal to this
    max_value = models.DecimalField(decimal_places=2, max_digits=10,default = 0)                 #trait value less than or equal to this

    def __str__(self):
        return "ID: " + str(self.id)

    class Meta:                
        verbose_name = 'Recruitment Trait Constraint'
        verbose_name_plural = 'Recruitment Trait Constraints'

    def json(self):
        return{
            "id":self.id,
            "name":f'{self.trait.name} {self.min_value}-{self.max_value}',
            "trait_name":self.trait.name,
            "trait_id":self.trait.id,
            "min_value":self.min_value,
            "max_value":self.max_value,
        }
