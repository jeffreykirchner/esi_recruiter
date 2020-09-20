from django.contrib import admin
from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ngettext
from django.contrib import messages
from main.forms import parametersForm
from django.contrib.admin import AdminSite
from django.utils.translation import ugettext_lazy
from django.conf import settings
from main.models import *
from main.views import sendMassEmailVerify

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

class parametersadmin(admin.ModelAdmin):
      def has_add_permission(self, request, obj=None):
            return False
      
      def has_delete_permission(self, request, obj=None):
            return False
      
      form = parametersForm

      actions = []

admin.site.register(parameters, parametersadmin)

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

            # queryset_active = queryset.filter(user__is_active=True).exclude(user__is_staff = True)

            queryset_active_profile = list(queryset.filter(user__is_active = True).exclude(user__is_staff = True).select_related('user'))
            updated_users = user_list.update(is_active = False)

            updated3 = sendMassEmailVerify(queryset_active_profile,request)

            #updated2 = queryset_active_profile.update(email_confirmed="no")
            #updated = queryset_active.update(is_active=False)            

            self.message_user(request, ngettext(
                  '%d user was deactivated.',
                  '%d users were deactivated.',
                  updated_users,
            ) % updated_users, messages.SUCCESS)

            # self.message_user(request, ngettext(
            #       '%d profile was deactivated.',
            #       '%d profiles were deactivated.',
            #       updated2,
            # ) % updated2, messages.SUCCESS)

            self.message_user(request,"Emails Sent: " + str(updated3['mailCount']) + " " + updated3['errorMessage'], messages.SUCCESS)

      deactivate_all.short_description = "Deactivate selected subjects and re-invite"

      #clear everyone from blackballs status
      def clear_blackBalls(self, request, queryset):

            updated = queryset.exclude(user__is_staff = 1).update(blackballed=0)

            self.message_user(request, ngettext(
                  '%d user was updated.',
                  '%d users were updated.',
                  updated,
            ) % updated, messages.SUCCESS)
      clear_blackBalls.short_description = "Remove blackballs"

      #confirm all active user's emails
      def confirm_active_email(self, request, queryset):

            updated = queryset.filter(user__is_active = 1).update(email_confirmed="yes")

            self.message_user(request, ngettext(
                  '%d user was updated.',
                  '%d users were updated.',
                  updated,
            ) % updated, messages.SUCCESS)
      confirm_active_email.short_description = "Manually confirm selected active user's emails"

      #clear everyone from blackballs status
      def un_confirm_emails(self, request, queryset):

            updated = queryset.exclude(user__is_staff = 1).update(email_confirmed='no')

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
                  c +=  p.setupemail_filter()
            
            self.message_user(request, ngettext(
                  '%d user was updated.',
                  '%d users were updated.',
                  c,
            ) % c, messages.SUCCESS)

      apply_email_filter.short_description = "Apply email filters to selected profiles"    

      ordering = ['user__last_name','user__first_name']
      search_fields = ['user__last_name','user__first_name','chapmanID','user__email']
      actions = [clear_blackBalls,confirm_active_email,un_confirm_emails,apply_email_filter,deactivate_all,activate_all]
      list_display = ['__str__','studentWorker','blackballed','email_filter']
      list_filter = ('blackballed', 'studentWorker','user__is_active','email_filter')


admin.site.unregister(User)
admin.site.register(User, UserAdmin)