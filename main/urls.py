from django.contrib import admin
from django.urls import path,re_path
from django.views.generic.base import RedirectView
from django.conf.urls import include,url
from django.conf import settings
from . import views

urlpatterns = [
    re_path(r'^admin/login/$', RedirectView.as_view(url=settings.LOGIN_URL, permanent=True, query_string=True)),    
    path('',views.mainHome,name='mainHome'),
    path('accounts/', include('django.contrib.auth.urls')),  #django built in account registrations
    path('profile/', views.profile,name='profile'), #custom profile         
    path('profileCreate/',views.profileCreate,name='profileCreate'),
    path('profileVerify/<token>/',views.profileVerify,name='profileVerify'),
    path('profileVerifyResend/<token>/',views.profileVerifyResend,name='profileVerifyResend'),
    path('urlLogin/<u>/<p>/<viewName>/',views.urlLogin,name='urlLogin'),
    path('userSearch/',views.userSearch,name='userSearch'),
    path('userInfo/<id>/',views.userInfo,name='userInfo'),
    path('fitBit/',views.fitBit,name='fitBit'),
]