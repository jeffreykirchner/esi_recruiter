from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.translation import ngettext
from django.contrib import messages

# Register your models here.
from main.models import *

admin.site.register(accounts)
admin.site.register(accountTypes)
admin.site.register(departments)
admin.site.register(genders)
admin.site.register(institutions)
admin.site.register(majors)
admin.site.register(schools)



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
            updated = queryset.exclude(is_staff = 1).update(is_active=0)
            self.message_user(request, ngettext(
                  '%d user was deactivated.',
                  '%d users were deactivated.',
                  updated,
            ) % updated, messages.SUCCESS)
      deactivate_all.short_description = "Deactivate selected subjects"

      ordering = ['last_name','first_name']
      search_fields = ['last_name','first_name','email']
      list_display = ['last_name', 'first_name','email','is_active','is_staff']
      actions = [activate_all,deactivate_all]
      list_filter = ('is_staff', 'is_active')

@admin.register(profile)
class ProfileAdmin(admin.ModelAdmin):      
      ordering = ['user__last_name','user__first_name']
      search_fields = ['user__last_name','user__first_name','chapmanID','user__email']


admin.site.unregister(User)
admin.site.register(User, UserAdmin)