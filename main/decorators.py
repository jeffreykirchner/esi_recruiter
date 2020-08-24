from django.core.exceptions import PermissionDenied
from django.conf import settings

from .models import profile

def user_is_staff(function):

    def wrap(request, *args, **kwargs):    
        #check for profile
        # if not request.user.profile:
        #     p = profile()
        #     p.chapmanID = 0000
        #     p.gender =  4
        #     p.labUser = 0
        #     p.user = request.user
        #     p.save()

        if request.user.profile.type.name=="staff":
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap

def user_is_subject(function):
    def wrap(request, *args, **kwargs):       
        if request.user.profile.type.name=="subject":
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap

def in_debug_mode(function):
    def wrap(request, *args, **kwargs):       
        if settings.DEBUG==True:
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap