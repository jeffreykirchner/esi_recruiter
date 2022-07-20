import logging

from django.contrib.auth import logout
from django.shortcuts import render
from django.views import View

class LogoutView(View):
    '''
    Log out view
    '''

    template_name = "registration/loggedOut.html"

    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''
        logger = logging.getLogger(__name__)     
        logger.info(f"Log out {request.user}")

        logout(request)

        return render(request,self.template_name,{})
    
