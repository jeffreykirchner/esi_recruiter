import json
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.views import View
from django.utils.decorators import method_decorator
from django.views.generic.detail import SingleObjectMixin

from main.decorators import user_is_staff

class SubjectAutoLogin(SingleObjectMixin, View):
    '''
    login as subject if elevated staff users
    '''

    model = User

    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    @method_decorator(staff_member_required)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logger = logging.getLogger(__name__)

        logout(request)
        login(request, self.get_object())

        return redirect('MainHome')
        