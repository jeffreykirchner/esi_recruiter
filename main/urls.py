'''
URLs for main app
'''

from django.urls import path, re_path
from django.views.generic.base import RedirectView
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from django.conf import settings
from django.templatetags.static import static

from .sitemaps import StaticViewSitemap

from main import views

sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    #admin site
    re_path(r'^admin/login/$', views.LoginView.as_view()),

    #account control
    path('', views.MainHome.as_view(), name='MainHome'),                           #direct user by subject type
    path('profile/', views.UpdateProfile.as_view(), name='profile'),               #view profile
    path('accounts/profile/', views.UpdateProfile.as_view(), name='profile2'),     #view profile
    path('profileCreate/', views.ProfileCreate.as_view(), name='profileCreate'),                      #create new profile 
    path('profilecreate/', views.ProfileCreate.as_view(), name='profileCreate2'),                     #create new profile 
    path('profileVerify/<str:token>/', views.ProfileVerify.as_view(), name='profileVerify'),          #verify email
    path('profileVerifyResend/', views.ProfileVerifyResend.as_view(), name='profileVerifyResend'),    #resend email verification
    
    path('accounts/login/', views.LoginView.as_view(), name="login"),
    path('accounts/passwordReset/', views.PasswordResetView.as_view(), name="passwordReset"),
    path('accounts/passwordResetChange/<str:token>', views.PasswordResetChangeView.as_view(), name="passwordResetChange"),
    path('accounts/logout/', views.LogoutView.as_view(), name="logout"),

    #staff
    path('userSearch/', views.UserSearch.as_view(), name='userSearch'),
    path('userSearchParameters/<int:id>/', views.UserSearchParametersView.as_view(), name='userSearchParameters_id'),
    path('userSearchParameters/', views.UserSearchParametersView.as_view(), name='userSearchParameters'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('userInfo/<int:pk>/', views.UserInfo.as_view(), name='userInfo'),
    path('experimentSearch/', views.ExperimentSearch.as_view(), name='experimentSearch'),
    path('experiment/<int:pk>/', views.ExperimentView.as_view(), name='experimentView'),
    path('experimentParameters/<int:pk>/', views.ExperimentParametersView.as_view(), name='experimentParametersView'),
    path('experimentSession/<int:pk>/', views.ExperimentSessionView.as_view(), name='experimentSessionView'),
    path('experimentSessionParameters/<int:pk>/', views.ExperimentSessionParametersView.as_view(), name='experimentSessionParametersView'),
    path('experimentSessionRun/<int:pk>/', views.ExperimentSessionRunView.as_view(), name='experimentSessionRunView'),
    path('experimentSessionPayouts/<int:pk>/<str:payGroup>/', views.ExperimentSessionPayoutsView.as_view(), name='experimentSessionPayoutsView'),
    path('calendar/<int:month>/<int:year>/', views.CalendarView.as_view(), name='calendarView_m_y'),
    path('calendar/', views.CalendarView.as_view(), name='calendarView'),
    path('traits/', views.TraitsView.as_view(), name='traits'),
    path('sessionsOpen/', views.SessionsOpen.as_view(), name='sessionsOpen'),
    path('paymentHistory/', views.PaymentHistory.as_view(), name='paymentHistory'),
    path('consentFormReport/', views.ConsentFormReport.as_view(), name='consentFormReport'),
    path('irbReport/', views.IrbReport.as_view(), name='irbReport'),
    path('subject-auto-login/<int:pk>/', views.SubjectAutoLogin.as_view(), name='subject_auto_login'),

    #subject
    path('subjectHome/', views.SubjectHome.as_view(), name='subjectHome'),
    path('subjectConsent/<int:id>/<str:type>/<str:view_mode>/', views.SubjectConsent.as_view(), name='subjectConsent'),
    path('subjectInvitation/<int:id>/', views.SubjectInvitation.as_view(), name='subjectInvitation'),
    path('faq/', views.FaqView.as_view(), name='faqView'),

    #cron
    path('runCrons/', csrf_exempt(views.RunCronsView.as_view()), name='runCronsView'),

    #txt
    path('robots.txt', views.RobotsTxt, name='robotsTxt'),
    path('ads.txt', views.AdsTxt, name='adsTxt'),
    path('.well-known/security.txt', views.SecurityTxt, name='securityTxt'),
    path('security.txt', views.SecurityTxt, name='securityTxt'),
    path('humans.txt', views.HumansTxt, name='humansTxt'),

    #icons
    path('favicon.ico', RedirectView.as_view(url=static('favicon.ico')), name='favicon1'),
    path('apple-touch-icon-precomposed.png', RedirectView.as_view(url=static('apple-touch-icon-precomposed.png')), name='favicon2'),
    path('apple-touch-icon.png', RedirectView.as_view(url=static('apple-touch-icon-precomposed.png')), name='favicon3'),
    path('apple-touch-icon-120x120-precomposed.png', RedirectView.as_view(url=static('apple-touch-icon-precomposed.png')), name='favicon4'),

    #google verification
    path('googleefdaedc1ef1e492e.html', RedirectView.as_view(url=static('googleefdaedc1ef1e492e.html')), name='google_verification'),

    #sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

]
