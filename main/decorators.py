from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.shortcuts import render
from main.forms import VerifyFormResend

from .models import profile

def user_is_staff(function):

    def wrap(request, *args, **kwargs):    

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

def email_confirmed(function):
    def wrap(request, *args, **kwargs):       
        if request.user.profile.email_confirmed=="yes":
            return function(request, *args, **kwargs)
        else:
            #email not verified redirect to verifiction resend          

            return render(request, 'registration/profile_verify_resend.html',{})

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