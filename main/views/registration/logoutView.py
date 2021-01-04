from django.contrib.auth import logout
from django.shortcuts import render

import logging

def logoutView(request):

    logger = logging.getLogger(__name__)     
    logger.info(f"Log out {request.user}")

    logout(request)

    return render(request,'registration/loggedOut.html',{})
    
