from django.contrib import admin
from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ngettext
from django.contrib import messages
from main.forms import parametersForm,faqForm,helpDocForm
from django.contrib.admin import AdminSite
from django.utils.translation import ugettext_lazy
from django.conf import settings
from main.models import *
from main.views import sendMassEmailVerify
from datetime import datetime,timedelta
import pytz
import logging
from django.db.models import Q,F,Value as V,Count
from django.contrib.auth.hashers import make_password

admin.site.register(accounts)
admin.site.register(account_types)
admin.site.register(departments)
admin.site.register(genders)
admin.site.register(institutions)
admin.site.register(majors)
admin.site.register(schools)
admin.site.register(email_filters)
admin.site.register(subject_types)


admin.site.site_header = settings.ADMIN_SITE_HEADER

class helpDocAdmin(admin.ModelAdmin):
            
      form = helpDocForm

      actions = []
      list_display = ['title','path']

admin.site.register(help_docs,helpDocAdmin)

class faqAdmin(admin.ModelAdmin):
            
      form = faqForm

      actions = []
      list_display = ['__str__','active']

admin.site.register(faq,faqAdmin)

class parametersadmin(admin.ModelAdmin):
      def has_add_permission(self, request, obj=None):
            return False
      
      def has_delete_permission(self, request, obj=None):
            return False
      
      form = parametersForm

      actions = []

admin.site.register(parameters, parametersadmin)

@admin.register(Traits)
class traitsAdmin(admin.ModelAdmin):
      ordering = ['name']

@admin.register(profile_trait)
class profile_traitAdmin(admin.ModelAdmin):
      ordering = ['my_profile__user__last_name','my_profile__user__first_name','trait__name']
      fields = ['value']

      search_fields = ['my_profile__user__first_name','my_profile__user__last_name','my_profile__studentID']

class UserAdmin(admin.ModelAdmin):

      ordering = ['last_name','first_name']
      search_fields = ['last_name','first_name','email']
      list_display = ['last_name', 'first_name','email','is_active','is_staff']
      actions = []
      list_filter = ('is_staff', 'is_active')

@admin.register(profile)
class ProfileAdmin(admin.ModelAdmin):

      def activate_all(self, request, queryset):

            user_list = User.objects.filter(profile__in = queryset).exclude(is_staff = True)
            updated_users = user_list.update(is_active = True)

            self.message_user(request, ngettext(
                  '%d user was activated.',
                  '%d users were activated.',
                  updated_users,
            ) % updated_users, messages.SUCCESS)
      activate_all.short_description = "Activate selected subjects"

      def deactivate_all(self, request, queryset):

            user_list = User.objects.filter(profile__in = queryset).filter(is_active=True).exclude(is_staff = True)      

            queryset_active_profile = list(queryset.filter(user__is_active = True).exclude(user__is_staff = True).select_related('user'))
            updated_users = user_list.update(is_active = False)

            updated3 = sendMassEmailVerify(queryset_active_profile,request)         

            self.message_user(request, ngettext(
                  '%d user was deactivated.',
                  '%d users were deactivated.',
                  updated_users,
            ) % updated_users, messages.SUCCESS)

            self.message_user(request,"Emails Sent: " + str(updated3['mailCount']) + " " + updated3['errorMessage'], messages.SUCCESS)

      deactivate_all.short_description = "Deactivate selected active subjects and re-invite"

      #clear everyone from blackballs status
      def clear_blackBalls(self, request, queryset):

            updated = queryset.exclude(user__is_staff = True).update(blackballed=0)

            self.message_user(request, ngettext(
                  '%d user was updated.',
                  '%d users were updated.',
                  updated,
            ) % updated, messages.SUCCESS)
      clear_blackBalls.short_description = "Remove blackballs"

      #confirm all active user's emails
      def confirm_active_email(self, request, queryset):

            updated = queryset.filter(user__is_active = True).update(email_confirmed="yes")

            self.message_user(request, ngettext(
                  '%d user was updated.',
                  '%d users were updated.',
                  updated,
            ) % updated, messages.SUCCESS)
      confirm_active_email.short_description = "Manually confirm selected active user's emails"

      #un confirm all selected email address
      def un_confirm_emails(self, request, queryset):

            updated = queryset.exclude(user__is_staff = True).update(email_confirmed='no')

            self.message_user(request, ngettext(
                  '%d user was updated.',
                  '%d users were updated.',
                  updated,
            ) % updated, messages.SUCCESS)
      un_confirm_emails.short_description = "Un-confirm selected email addresses"

      #apply email filter to profile
      def apply_email_filter(self,request,queryset):

            c = 0
            for p in queryset:
                  c +=  p.setup_email_filter()
            
            self.message_user(request, ngettext(
                  '%d user was updated.',
                  '%d users were updated.',
                  c,
            ) % c, messages.SUCCESS)
      apply_email_filter.short_description = "Apply email filters to selected profiles" 

      #require all selected users to agree to consent form before attending another experiment
      def consent_form_required(self, request, queryset):

            updated = queryset.exclude(user__is_staff = True).update(consentRequired=True)

            self.message_user(request, ngettext(
                  '%d user was updated.',
                  '%d users were updated.',
                  updated,
            ) % updated, messages.SUCCESS)
      consent_form_required.short_description = "Require selected users to agree to consent form"

      #activate users who were attended within last two years
      def activate_recent_users(self, request, queryset):
            logger = logging.getLogger(__name__)
            logger.info("activate_recent_users")

            d_now_minus_two_years = datetime.now(pytz.utc) - timedelta(days=730)

            qs = experiment_session_day_users.objects.filter(Q(attended = True) | Q(bumped = True))\
                                             .filter(experiment_session_day__date__gte = d_now_minus_two_years)\
                                             .values_list("user__id",flat=True)

            logger.info("Number of users found: " + str(len(qs)))

            q_list = queryset.filter(user__id__in = qs)
            updated = User.objects.filter(profile__in = q_list).update(is_active = True)

            self.message_user(request, ngettext(
                  '%d user was updated.',
                  '%d users were updated.',
                  updated,
            ) % updated, messages.SUCCESS)
      activate_recent_users.short_description = "Activate users who attended in past two years"   

      #set selected users up to be test subejects

      def setup_test_users(self, request, queryset):
            logger = logging.getLogger(__name__)
            logger.info("setup_test_users")

            updated = queryset.exclude(user__is_staff = True).update(consentRequired=False,
                                                                     blackballed=False,
                                                                     email_confirmed='yes',
                                                                     paused=False)
            
            pw =  make_password("esi2008esi")
            for p in queryset.exclude(user__is_staff = True):
                  p.user.password = pw
                  p.user.is_active=True
                  p.user.save()
                 
            self.message_user(request, ngettext(
                  '%d user was updated.',
                  '%d users were updated.',
                  updated,
            ) % updated, messages.SUCCESS)
      setup_test_users.short_description = "Setup users as test subjects, pw = 'esi2008esi'."

      ordering = ['user__last_name','user__first_name']
      search_fields = ['user__last_name','user__first_name','studentID','user__email']
      actions = [clear_blackBalls,confirm_active_email,un_confirm_emails,apply_email_filter,
                 deactivate_all,activate_all,consent_form_required,activate_recent_users,setup_test_users]
      list_display = ['__str__','studentWorker','blackballed','email_filter']
      list_filter = ('blackballed', 'studentWorker','user__is_active','email_filter')     


admin.site.unregister(User)
admin.site.register(User, UserAdmin)