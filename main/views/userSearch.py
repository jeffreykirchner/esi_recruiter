from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
import json
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import CharField,Q,F,Value as V
from django.db.models.functions import Lower,Concat
from django.urls import reverse
from main import views

@login_required
@user_is_staff
def userSearch(request):
    if request.method == 'POST':

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getUsers":
            request.session['userSearchTerm'] = data["searchInfo"]            

            users= lookup(data["searchInfo"])

            return JsonResponse({"users" :  users},safe=False)
        elif data["action"] == "deleteUser":
            uid = data["uid"]
            u=User.objects.get(id=uid)
            u.delete()

            users= lookup(request.session['userSearchTerm'])
            return JsonResponse({"users" :  users},safe=False)
    else:
        return render(request,'userSearch.html',{})      

def lookup(value):
    users=User.objects.order_by(Lower('last_name'),Lower('first_name')) \
                      .filter(Q(last_name__icontains = value) |
                              Q(first_name__icontains = value) |
                              Q(email__icontains = value) |
                              Q(profile__chapmanID__icontains = value) |
                              Q(profile__type__name__icontains = value)) \
                      .values("id","first_name","last_name","email","profile__chapmanID","profile__type__name")

    print(json.dumps(list(users),cls=DjangoJSONEncoder))

    return json.dumps(list(users),cls=DjangoJSONEncoder)
