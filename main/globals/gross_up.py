
'''
gross up payment to cover tax payment
'''
from decimal import Decimal
import logging

from main.models import Parameters

def gross_up(payment):
    '''
    gross up payments
    '''
    p = Parameters.objects.first()

    return (payment / (1 - p.international_tax_rate)) * p.international_tax_rate 