
'''
format minutes to hours and minutes
'''
import  math
import logging

def format_minutes(minutes) -> str:
    '''
    format minutes to hours and minutes
    '''
    logger = logging.getLogger(__name__)
    
    # v = f'{math.floor(minutes/60)}'

    # if v == "1":
    #     v += "hr "
    # else:
    #     v += "hrs "

    # if minutes%60 != 0 :

    #     if v == "0hrs ":
    #         v = f'{minutes%60}'
    #     else:
    #         v += f' {minutes%60}'

    #     if minutes%60 == 1:
    #         v += "min"
    #     else:
    #          v += "mins"
    
    #logger.info(f'format_minutes: {minutes}, {v}')

    hours = math.floor(minutes / 60)
    mins = minutes % 60

    v = ""

    if hours > 0:
        v += f'{hours}hr ' if hours == 1 else f'{hours}hrs '

    if mins != 0:
        v += f'{mins}min' if mins == 1 else f'{mins}mins'

    if v == "":
        v = "0mins"

    return v