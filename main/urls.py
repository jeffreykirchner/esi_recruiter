from django.contrib import admin
from django.urls import path,re_path
from django.views.generic.base import RedirectView
from django.conf.urls import include,url
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from main.views import *

urlpatterns = [
    #admin site
    # re_path(r'^admin/login/$',\
    #         RedirectView.as_view(url=settings.LOGIN_URL,permanent=True,query_string=True)),    

    re_path(r'^admin/login/$',views.loginView),

    #account control
    path('',views.mainHome,name='mainHome'),                 #direct user by subject type
    path('profile/', views.updateProfile,name='profile'),    #custom profile 
    path('accounts/profile/', views.updateProfile,name='profile'), #custom profile         
    path('profileCreate/',views.profileCreate,name='profileCreate'),
    path('profileVerify/<token>/',views.profileVerify,name='profileVerify'),
    path('profileVerifyResend/',views.profileVerifyResend,name='profileVerifyResend'),
    
    path('accounts/login/',views.loginView,name="login"),
    path('accounts/passwordReset/',views.passwordResetView,name="passwordReset"),
    path('accounts/passwordResetChange/<token>',views.passwordResetChangeView,name="passwordResetChange"),
    path('accounts/logout/',views.logoutView,name="logout"),
    
    #staff
    path('userSearch/',views.userSearch,name='userSearch'),
    path('reports/',views.reportsView,name='reports'),
    path('userInfo/<id>/',views.userInfo,name='userInfo'),
    path('experimentSearch/',views.experimentSearch,name='experimentSearch'),
    path('experiment/<id>/',views.experimentView,name='experimentView'),
    path('experimentSession/<id>/',views.experimentSessionView,name='experimentSessionView'),
    path('experimentSessionRun/<id>/',views.experimentSessionRunView,name='experimentSessionRunView'),
    path('experimentSessionPayouts/<id>/<payGroup>/',views.experimentSessionPayoutsView,name='experimentSessionPayoutsView'),
    path('calendar/',views.calendarView,name='calendarView'),
    path('traits/',views.traitsView,name='traits'),

    #subject
    path('subjectHome/',views.subjectHome,name='subjectHome'),
    path('faq/',views.faqView,name='faqView'),

    #cron
    path('runCrons/',csrf_exempt(views.runCronsView),name='runCronsView'),

    #bots
    path('robots.txt',views.RobotsTxt,name='robotsTxt'),
    path('ads.txt',views.AdsTxt,name='adsTxt'),


]
