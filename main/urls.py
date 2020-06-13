from django.contrib import admin
from django.urls import path,re_path
from django.views.generic.base import RedirectView
from django.conf.urls import include,url
from django.conf import settings
from . import views

urlpatterns = [
    #admin site
    re_path(r'^admin/login/$', RedirectView.as_view(url=settings.LOGIN_URL, permanent=True, query_string=True)),    

    #account control
    path('',views.mainHome,name='mainHome'),
    path('accounts/', include('django.contrib.auth.urls')),  #django built in account registrations
    path('profile/', views.updateProfile,name='profile'), #custom profile         
    path('profileCreate/',views.profileCreate,name='profileCreate'),
    path('profileVerify/<token>/',views.profileVerify,name='profileVerify'),
    path('profileVerifyResend/<token>/',views.profileVerifyResend,name='profileVerifyResend'),
    
    #staff
    path('userSearch/',views.userSearch,name='userSearch'),
    path('userInfo/<id>/',views.userInfo,name='userInfo'),
    path('experiment/<id>/',views.experimentView,name='experimentView'),
    path('experimentSession/<id>/',views.experimentSessionView,name='experimentSessionView'),

    #subject
]