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
admin.site.register(accountTypes)
admin.site.register(departments)
admin.site.register(genders)
admin.site.register(institutions)
admin.site.register(majors)
admin.site.register(schools)

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

      def activate_all(self, request, queryset):
            updated = queryset.exclude(is_staff = 1).update(is_active=1)
            self.message_user(request, ngettext(
                  '%d user was activated.',
                  '%d users were activated.',
                  updated,
            ) % updated, messages.SUCCESS)
      activate_all.short_description = "Activate selected subjects"

      def deactivate_all(self, request, queryset):
            queryset_active = queryset.filter(is_active=True).exclude(is_staff = True)
            queryset_active_profile = profile.objects.filter(user__in = queryset_active).select_related('user')

            updated3 = sendMassEmailVerify(queryset_active_profile,request)

            #updated2 = queryset_active_profile.update(emailConfirmed="no")
            updated = queryset_active.update(is_active=False)            

            self.message_user(request, ngettext(
                  '%d user was deactivated.',
                  '%d users were deactivated.',
                  updated,
            ) % updated, messages.SUCCESS)

            # self.message_user(request, ngettext(
            #       '%d profile was deactivated.',
            #       '%d profiles were deactivated.',
            #       updated2,
            # ) % updated2, messages.SUCCESS)

            self.message_user(request,"Emails Sent: " + str(updated3['mailCount']) + " " + updated3['errorMessage'], messages.SUCCESS)

      deactivate_all.short_description = "Deactivate selected subjects and re-invite"

      ordering = ['last_name','first_name']
      search_fields = ['last_name','first_name','email']
      list_display = ['last_name', 'first_name','email','is_active','is_staff']
      actions = [activate_all,deactivate_all]
      list_filter = ('is_staff', 'is_active')

@admin.register(profile)
class ProfileAdmin(admin.ModelAdmin):
      def clear_blackBalls(self, request, queryset):

            updated = queryset.exclude(user__is_staff = 1).update(blackballed=0)

            self.message_user(request, ngettext(
                  '%d user was updated.',
                  '%d users were updated.',
                  updated,
            ) % updated, messages.SUCCESS)
      clear_blackBalls.short_description = "Remove blackballs"

      ordering = ['user__last_name','user__first_name']
      search_fields = ['user__last_name','user__first_name','chapmanID','user__email']
      actions = [clear_blackBalls]
      list_display = ['__str__','studentWorker','blackballed']
      list_filter = ('blackballed', 'studentWorker')


admin.site.unregister(User)
admin.site.register(User, UserAdmin)