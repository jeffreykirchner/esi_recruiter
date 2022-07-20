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
    path('profileVerify/<str:token>/', views.ProfileVerify.as_view(), name='profileVerify'),          #verify email
    path('profileVerifyResend/', views.ProfileVerifyResend.as_view(), name='profileVerifyResend'),    #resend email verification
    
    path('accounts/login/', views.LoginView.as_view(), name="login"),
    path('accounts/passwordReset/', views.PasswordResetView.as_view(), name="passwordReset"),
    path('accounts/passwordResetChange/<str:token>', views.PasswordResetChangeView.as_view(), name="passwordResetChange"),
    path('accounts/logout/', views.LogoutView.as_view(), name="logout"),

    #staff
    path('userSearch/', views.userSearch, name='userSearch'),
    path('userSearchParameters/<int:id>/', views.userSearchParametersView, name='userSearchParameters_id'),
    path('userSearchParameters/', views.userSearchParametersView, name='userSearchParameters'),
    path('reports/', views.reportsView, name='reports'),
    path('userInfo/<int:id>/', views.userInfo, name='userInfo'),
    path('experimentSearch/', views.experimentSearch, name='experimentSearch'),
    path('experiment/<int:id>/', views.experimentView, name='experimentView'),
    path('experimentParameters/<int:id>/', views.experimentParametersView, name='experimentParametersView'),
    path('experimentSession/<int:id>/', views.experimentSessionView, name='experimentSessionView'),
    path('experimentSessionParameters/<int:id>/', views.experimentSessionParametersView, name='experimentSessionParametersView'),
    path('experimentSessionRun/<int:id_>/', views.experimentSessionRunView, name='experimentSessionRunView'),
    path('experimentSessionPayouts/<int:id>/<payGroup>/', views.experimentSessionPayoutsView, name='experimentSessionPayoutsView'),
    path('calendar/<int:month>/<int:year>/', views.calendarView, name='calendarView_m_y'),
    path('calendar/', views.calendarView, name='calendarView'),
    path('traits/', views.traitsView, name='traits'),
    path('sessionsOpen/', views.SessionsOpen, name='sessionsOpen'),
    path('paymentHistory/', views.PaymentHistory, name='paymentHistory'),
    path('subject-auto-login/<int:id>/', views.SubjectAutoLogin, name='subject_auto_login'),

    #subject
    path('subjectHome/', views.subjectHome, name='subjectHome'),
    path('subjectConsent/<int:id>/', views.subjectConsent, name='subjectConsent'),
    path('subjectInvitation/<int:id>/', views.subjectInvitation, name='subjectInvitation'),
    path('faq/', views.faqView, name='faqView'),

    #cron
    path('runCrons/', csrf_exempt(views.runCronsView), name='runCronsView'),

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
    path('apple-touch-icon-120x120-precomposed.png', RedirectView.as_view(url=static('settings.STATIC_URL}apple-touch-icon-precomposed.png')), name='favicon4'),

    #google verification
    path('googleefdaedc1ef1e492e.html', RedirectView.as_view(url=static('googleefdaedc1ef1e492e.html')), name='google_verification'),

    #sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

]
