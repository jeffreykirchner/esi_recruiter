'''
URLs for main app
'''

from django.urls import path, re_path
from django.views.generic.base import RedirectView

from django.views.decorators.csrf import csrf_exempt
from main import views
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap

sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    #admin site
    # re_path(r'^admin/login/$',\
    #         RedirectView.as_view(url=settings.LOGIN_URL,permanent=True,query_string=True)),    

    re_path(r'^admin/login/$', views.loginView),

    #account control
    path('', views.mainHome, name='mainHome'),                           #direct user by subject type
    path('profile/', views.updateProfile, name='profile'),              #custom profile
    path('accounts/profile/', views.updateProfile, name='profile'),     #custom profile
    path('profileCreate/', views.profileCreate, name='profileCreate'),
    path('profileVerify/<token>/', views.profileVerify, name='profileVerify'),
    path('profileVerifyResend/', views.profileVerifyResend, name='profileVerifyResend'),
    
    path('accounts/login/', views.loginView, name="login"),
    path('accounts/passwordReset/', views.passwordResetView, name="passwordReset"),
    path('accounts/passwordResetChange/<token>', views.passwordResetChangeView, name="passwordResetChange"),
    path('accounts/logout/', views.logoutView, name="logout"),

    #staff
    path('userSearch/', views.userSearch, name='userSearch'),
    path('reports/', views.reportsView, name='reports'),
    path('userInfo/<id>/', views.userInfo, name='userInfo'),
    path('experimentSearch/', views.experimentSearch, name='experimentSearch'),
    path('experiment/<id>/', views.experimentView, name='experimentView'),
    path('experimentSession/<id>/', views.experimentSessionView, name='experimentSessionView'),
    path('experimentSessionRun/<id_>/', views.experimentSessionRunView, name='experimentSessionRunView'),
    path('experimentSessionPayouts/<id>/<payGroup>/', views.experimentSessionPayoutsView, name='experimentSessionPayoutsView'),
    path('calendar/<int:month>/<int:year>/', views.calendarView, name='calendarView'),
    path('calendar/', views.calendarView, name='calendarView'),
    path('traits/', views.traitsView, name='traits'),
    path('sessionsOpen/', views.SessionsOpen, name='sessionsOpen'),
    path('payPalHistory/', views.PayPalHistory, name='payPalHistory'),
    path('subject-auto-login/<int:id>/', views.SubjectAutoLogin, name='subject_auto_login'),

    #subject
    path('subjectHome/', views.subjectHome, name='subjectHome'),
    path('faq/', views.faqView, name='faqView'),

    #cron
    path('runCrons/', csrf_exempt(views.runCronsView), name='runCronsView'),

    #txt
    path('robots.txt', views.RobotsTxt, name='robotsTxt'),
    path('ads.txt', views.AdsTxt, name='adsTxt'),
    path('.well-known/security.txt', views.SecurityTxt, name='securityTxt'),
    path('humans.txt', views.HumansTxt, name='humansTxt'),

    #icons
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico'), name='favicon'),
    path('apple-touch-icon-precomposed.png', RedirectView.as_view(url='/static/apple-touch-icon-precomposed.png'), name='favicon'),
    path('apple-touch-icon.png', RedirectView.as_view(url='/static/apple-touch-icon-precomposed.png'), name='favicon'),
    path('apple-touch-icon-120x120-precomposed.png', RedirectView.as_view(url='/static/apple-touch-icon-precomposed.png'), name='favicon'),

    #sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

]
