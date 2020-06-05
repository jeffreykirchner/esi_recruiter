from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required
def mainHome(request):
    if request.method == 'POST':
         return JsonResponse({"Fail" : "Fail"}, safe=False)
    else:
        pass

        return render(request,'mainHome.html',{'user':request.user})    