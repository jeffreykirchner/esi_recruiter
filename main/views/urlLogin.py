from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.shortcuts import render

def urlLogin(request,u,p,viewName):
    if request.method == 'GET':
        user = authenticate(request,username=u,password=p)

    if user is not None:
        login(request,user)
        return redirect(viewName)
    else:
        return render(request,'urlLogin.html',{})

