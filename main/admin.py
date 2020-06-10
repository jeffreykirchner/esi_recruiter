from django.contrib import admin

# Register your models here.
from main.models import *

admin.site.register(accounts)
admin.site.register(accountTypes)
admin.site.register(departments)
admin.site.register(genders)
admin.site.register(institutions)
admin.site.register(majors)
admin.site.register(schools)

@admin.register(profile)
class ProfileAdmin(admin.ModelAdmin):
      ordering = ['user__last_name']
      search_fields = ['user__last_name','user__first_name','chapmanID','user__email']