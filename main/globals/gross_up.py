
'''
gross up payment to cover tax payment
'''
from decimal import Decimal
import imp
import logging

from main.models import parameters

def gross_up(payment):
    '''
    gross up payments
    '''
    p = parameters.objects.first()

    return (payment / (1 - p.international_tax_rate)) * p.international_tax_rate 