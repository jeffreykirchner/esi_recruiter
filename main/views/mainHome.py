from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from main.decorators import email_confirmed
from django.http import JsonResponse
from django.shortcuts import redirect

@login_required
@email_confirmed
def mainHome(request):
    if request.method == 'POST':
         return JsonResponse({"Fail" : "Fail"}, safe=False)
    else:
        pass

        if request.user.profile.type.id == 1:
            return redirect('calendarView')
        else:
            return redirect('subjectHome')    