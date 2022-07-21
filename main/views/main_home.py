
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.generic import View
from django.utils.decorators import method_decorator

from main.decorators import email_confirmed

class MainHome(View):
    '''
    Direct user by type their home view.
    '''
    
    @method_decorator(login_required)
    @method_decorator(email_confirmed)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        if request.user.profile.type.id == 1:
            return redirect('calendarView')
        else:
            return redirect('subjectHome')

            