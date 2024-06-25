'''
admin site
'''

from datetime import datetime, timedelta

import pytz
import logging

from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.translation import ngettext
from django.contrib import messages
from django.conf import settings
from django.db.models import Q,F,Value as V,Count
from django.contrib.auth.hashers import make_password
from django.db.models.functions import Lower
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from django.db.backends.postgresql.psycopg_any import DateTimeTZRange
from django.utils import timezone

from main.models import *

from main.globals import todays_date

from main.forms import ParametersForm
from main.forms import FaqForm
from main.forms import HelpDocForm
from main.forms import FrontPageNoticeForm
from main.forms import InvitationEmailTemplateForm

import main

class ExperimentSessionInline(admin.TabularInline):
      '''
      experiment session inline
      '''
      def has_add_permission(self, request, obj=None):
        return False

      def has_change_permission(self, request, obj=None):
        return False

      extra = 0  
      model = ExperimentSessions
      can_delete = False
      show_change_link = True
      fields=('creator','consent_form')

class ExperimentSessionDayInline(admin.TabularInline):
      '''
      experiment session day inline
      '''
      def has_add_permission(self, request, obj=None):
        return False

      def has_change_permission(self, request, obj=None):
        return False

      extra = 0  
      model = ExperimentSessionDays
      can_delete = False
      show_change_link = True
      fields=('date','length', 'complete')

@admin.register(Accounts)
class AccountsAdmin(admin.ModelAdmin):
    search_fields = ['name', 'number']
    list_display = [ 'number', 'name', 'department', 'archived', 'outside_funding']
    #inlines = [ExperimentSessionDayInline]

class AccountsInline(admin.TabularInline):

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    extra = 0  
    model = Accounts
    can_delete = True   
    show_change_link = True
    readonly_fields = ['number', 'name', 'archived', 'outside_funding']
    fields = ['number', 'name', 'archived', 'outside_funding']

@admin.register(Departments)
class AccountsAdmin(admin.ModelAdmin):
    search_fields = ['name', 'charge_account']
    list_display = [ 'name', 'charge_account', 'petty_cash']
    inlines = [AccountsInline]

admin.site.register(Genders)
admin.site.register(Institutions)
admin.site.register(Majors)
admin.site.register(Schools)
admin.site.register(EmailFilters)
admin.site.register(SubjectTypes)
admin.site.register(IrbStudy)
admin.site.register(Locations)

admin.site.site_header = settings.ADMIN_SITE_HEADER

@admin.register(ConsentForm)
class ConsentFormAdmin(admin.ModelAdmin):

      def duplicate(self, request, queryset):

            for consent_form in queryset.all():
                  obj, created=ConsentForm.objects.get_or_create(name=f'{consent_form.name} (copy)')
                 
                  obj.from_dict(dict(consent_form.json()), consent_form.pdf_file, consent_form.irb_study)

            self.message_user(request, ngettext(
                  '%d consent form was duplicated.',
                  '%d conent forms were duplicated.',
                  queryset.count(),
            ) % queryset.count(), messages.SUCCESS)

      duplicate.short_description = "Duplicate Consent Form"

      ordering = ['-updated']

      actions = ['duplicate']
      search_fields = ['name','irb_study__name','irb_study__number', 'pdf_file']
      list_display = ['name','pdf_file','irb_study', 'signature_required','agreement_required','archived','updated','timestamp']

@admin.register(UmbrellaConsentForm)
class UmbrellaConsentFormAdmin(admin.ModelAdmin):

      ordering = [Lower('display_name')]

      actions = []
      list_display = ['display_name','active','updated','timestamp']

@admin.register(HelpDocs)
class helpDocAdmin(admin.ModelAdmin):
            
      form = HelpDocForm

      ordering = [Lower('title')]

      actions = []
      list_display = ['title','path']

@admin.register(FrontPageNotice)
class frontPageNoticeAdmin(admin.ModelAdmin):
            
      form = FrontPageNoticeForm

      ordering = [Lower('subject_text')]

      actions = []
      list_display = ['subject_text','enabled']

@admin.register(InvitationEmailTemplates)
class invitationEmailTemplateAdmin(admin.ModelAdmin):
            
      form = InvitationEmailTemplateForm

      ordering = [Lower('name')]

      actions = []
      list_display = ['name','enabled']

@admin.register(FAQ)
class faqAdmin(admin.ModelAdmin):
            
      form = FaqForm

      actions = []
      list_display = ['__str__','active']

@admin.register(Parameters)
class parametersadmin(admin.ModelAdmin):
      def has_add_permission(self, request, obj=None):
            return False
      
      def has_delete_permission(self, request, obj=None):
            return False
      
      form = ParametersForm

      actions = []

@admin.register(Traits)
class traitsAdmin(admin.ModelAdmin):
      ordering = [Lower('name')]
      actions = ['archive']
      list_display = ['name', 'description', 'archived']
      search_fields = ['name']
      list_filter = ['archived']

      def archive(self, request, queryset):

            updated_traits = queryset.update(archived=True)

            self.message_user(request, ngettext(
                  '%d trait was archived.',
                  '%d traits were archived.',
                  updated_traits,
            ) % updated_traits, messages.SUCCESS)
      archive.short_description = "Archive selected traits"

@admin.register(profile_trait)
class profile_traitAdmin(admin.ModelAdmin):
      def get_queryset(self, request):
        qs = super(profile_traitAdmin, self).get_queryset(request)
        return qs.filter(archived=False)

      ordering = ['timestamp']
      fields = ['value']
      list_display = ['my_profile', 'trait', 'value', 'timestamp']
      search_fields = ['my_profile__user__first_name','my_profile__user__last_name','my_profile__studentID']

@admin.register(ProfileConsentForm)
class ProfileConsentFormAdmin(admin.ModelAdmin):
      

      ordering = ['-timestamp']
      fields = ['my_profile', 'consent_form', 'signature_points', 'singnature_resolution', 'timestamp']
      readonly_fields = ['my_profile', 'consent_form', 'signature_points', 'singnature_resolution', 'timestamp']
      list_display = ['my_profile', 'consent_form', 'timestamp']
      

#consent form inline
class ProfileConsentFormInline(admin.TabularInline):
      '''
      profile consent form inline
      '''
      def has_add_permission(self, request, obj=None):
        return False

      def has_change_permission(self, request, obj=None):
        return False

      extra = 0  
      model = ProfileConsentForm
      can_delete = True
      show_change_link = True
      fields=('consent_form',)

#consent form inline
class ProfileTraitsInline(admin.TabularInline):
      '''
      profile traits inline
      '''
      def has_add_permission(self, request, obj=None):
        return False

      def has_change_permission(self, request, obj=None):
        return False

      extra = 0  
      model = profile_trait
      can_delete = True
      show_view_link = True
      fields=('trait','value')

#profile login attempt inline
class ProfileLoginAttemptInline(admin.TabularInline):
      '''
      profile login attempt inline
      '''
      def get_queryset(self, request):
            qs = super().get_queryset(request)
            
            return qs.filter(timestamp__contained_by=DateTimeTZRange(timezone.now() - datetime.timedelta(days=30), timezone.now()))
      
      def has_add_permission(self, request, obj=None):
            return False

      def has_change_permission(self, request, obj=None):
            return False

      extra = 0  
      model = ProfileLoginAttempt
      can_delete = True
      fields=('success','note')
      readonly_fields = ('timestamp',)
      

class UserAdmin(DjangoUserAdmin):

      ordering = ['-date_joined']
      search_fields = ['last_name', 'first_name', 'email']
      list_display = ['last_name', 'first_name', 'email', 'date_joined', 'last_login']
      actions = []
      list_filter = ['profile__type', 'is_staff']

class NoLoginIn400Days(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('no login in last N days')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'user__last_login'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('400', _('400 days')),
            ('300', _('300 days')),
            ('200', _('200 days')),
            ('100', _('100 days')),
        )

    def queryset(self, request, queryset):
      """
      Returns the filtered queryset based on the value
      provided in the query string and retrievable via
      `self.value()`.
      """

      if self.value() == '400':
            today_minus_400 =  todays_date() - timedelta(days=400)

            return queryset.filter(
                  user__last_login__lte=today_minus_400,
            )

      if self.value() == '300':
            today_minus_300 =  todays_date() - timedelta(days=300)

            return queryset.filter(
                  user__last_login__lte=today_minus_300,
            )
      
      if self.value() == '200':
            today_minus_200 =  todays_date() - timedelta(days=200)

            return queryset.filter(
                  user__last_login__lte=today_minus_200,
            )
      
      if self.value() == '100':
            today_minus_100 =  todays_date() - timedelta(days=100)

            return queryset.filter(
                  user__last_login__lte=today_minus_100,
            )
        
@admin.register(profile)
class ProfileAdmin(admin.ModelAdmin):
      
      def deactivate_all(self, request, queryset):

            # user_list = User.objects.filter(profile__in = queryset)
            updated_users = queryset.update(disabled = True)

            self.message_user(request, ngettext(
                  '%d user was disabled.',
                  '%d users were disabled.',
                  updated_users,
            ) % updated_users, messages.SUCCESS)
      deactivate_all.short_description = "Disable selected users"

      def activate_all(self, request, queryset):

            # user_list = User.objects.filter(profile__in = queryset)
            updated_users = queryset.update(disabled = False)

            self.message_user(request, ngettext(
                  '%d user was enabled.',
                  '%d users were enabled.',
                  updated_users,
            ) % updated_users, messages.SUCCESS)
      activate_all.short_description = "Enable selected users"

      def pause_all(self, request, queryset):

            profile_list = queryset.exclude(user__is_staff=True) 

            #queryset_active_profile = list(queryset.filter(user__is_active=True).exclude(user__is_staff=True).select_related('user'))
            profile_list.update(paused=True)

            #updated3 = send_mass_email_verify(profile_list, request)         

            self.message_user(request, ngettext(
                  '%d user was paused.',
                  '%d users were paused.',
                  len(profile_list),
            ) % len(profile_list), messages.SUCCESS)

            #self.message_user(request, "Emails Sent: " + str(updated3['mail_count']) + " " + updated3['error_message'], messages.SUCCESS)

      pause_all.short_description = "Pause selected accounts"

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

      #activate users who were attended within last two years
      # def activate_recent_users(self, request, queryset):
      #       logger = logging.getLogger(__name__)
      #       logger.info("activate_recent_users")

      #       d_now_minus_two_years = datetime.now(pytz.utc) - timedelta(days=730)

      #       qs = ExperimentSessionDayUsers.objects.filter(Q(attended = True) | Q(bumped = True))\
      #                                        .filter(experiment_session_day__date__gte = d_now_minus_two_years)\
      #                                        .values_list("user__id",flat=True)

      #       logger.info("Number of users found: " + str(len(qs)))

      #       q_list = queryset.filter(user__id__in = qs)
      #       updated = User.objects.filter(profile__in = q_list).update(is_active = True)

      #       self.message_user(request, ngettext(
      #             '%d user was updated.',
      #             '%d users were updated.',
      #             updated,
      #       ) % updated, messages.SUCCESS)
      # activate_recent_users.short_description = "Activate users who attended in past two years"   

      #set selected users up to be test subejects
      def setup_test_users(self, request, queryset):
            logger = logging.getLogger(__name__)
            logger.info("setup_test_users")

            updated = queryset.exclude(user__is_staff = True).update(blackballed=False,
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

      def remove_international_status(self, request, queryset):

            updated = queryset.update(international_student=False)
            
            self.message_user(request, ngettext(
                  '%d user was updated.',
                  '%d users were updated.',
                  updated,
            ) % updated, messages.SUCCESS)
      remove_international_status.short_description = "Remove international status."

      @admin.display(boolean=True, description="Active")
      def get_user_is_active(self, obj):
            '''
            return active status of user
            '''
            return obj.user.is_active

      ordering = ['user__last_name','user__first_name']
      search_fields = ['user__last_name','user__first_name','studentID','user__email']
      actions = [clear_blackBalls, confirm_active_email, un_confirm_emails, apply_email_filter,
                 pause_all, deactivate_all, activate_all, remove_international_status]

      if settings.DEBUG:
            actions.append(setup_test_users)

      list_display = ['__str__', 'paused', 'disabled', 'email_filter', 'updated', 'last_login']
      list_filter = ('blackballed', 'email_filter', 'international_student', 'paused', 'user__last_login', 'type', 'disabled', NoLoginIn400Days)
      readonly_fields = ['user', 'password_reset_key', 'public_id']
      inlines = [ProfileConsentFormInline, ProfileTraitsInline, ProfileLoginAttemptInline]

      def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        form.base_fields['type'].widget.can_change_related = False
        form.base_fields['type'].widget.can_add_related = False

        form.base_fields['school'].widget.can_change_related = False
        form.base_fields['school'].widget.can_add_related = False

        form.base_fields['major'].widget.can_change_related = False
        form.base_fields['major'].widget.can_add_related = False

        form.base_fields['gender'].widget.can_change_related = False
        form.base_fields['gender'].widget.can_add_related = False

        form.base_fields['subject_type'].widget.can_change_related = False
        form.base_fields['subject_type'].widget.can_add_related = False

        form.base_fields['email_filter'].widget.can_change_related = False
        form.base_fields['email_filter'].widget.can_add_related = False

        return form

@admin.register(DailyEmailReport)
class DailyEmailReportAdmin(admin.ModelAdmin):
      def has_add_permission(self, request, obj=None):
            return False

      readonly_fields=('text',)

      ordering = ['-date']

#Experiment session day admin
@admin.register(ExperimentSessionDayUsers)
class ExperimentSessionDaysAdmin(admin.ModelAdmin):
      def has_delete_permission(self, request, obj=None):
            return False
      
      def has_add_permission(self, request, obj=None):
            return False
      
      readonly_fields=('experiment_session_day', 'addedByUser', 'user')

class ExperimentSessionDayUserInline(admin.TabularInline):
      '''
      experiment session day user inline
      '''
      def has_add_permission(self, request, obj=None):
        return False

      def has_change_permission(self, request, obj=None):
        return False
      
      def get_queryset(self, request):
        qs = super().get_queryset(request)
       
        return qs.filter(confirmed=True)

      extra = 0  
      model = ExperimentSessionDayUsers
      can_delete = False
      show_change_link = True
      fields=('user','attended', 'bumped','show_up_fee','earnings')

#Experiment session day admin
@admin.register(ExperimentSessionDays)
class ExperimentSessionDaysAdmin(admin.ModelAdmin):
      def has_delete_permission(self, request, obj=None):
            return False
      
      def has_add_permission(self, request, obj=None):
            return False

      readonly_fields=('experiment_session','user_who_paypal_api','users_who_paypal_paysheet','users_who_printed_paysheet','users_who_printed_bumps')
      
      inlines = [ExperimentSessionDayUserInline]
      search_fields = ['id','experiment_session__experiment__title',]
      #list_display = [']

#Experiment session day admin
@admin.register(ExperimentSessionInvitations)
class ExperimentSessionInvitationsAdmin(admin.ModelAdmin):
      def has_delete_permission(self, request, obj=None):
            return False
      
      def has_add_permission(self, request, obj=None):
            return False
      
      def has_change_permission(self, request, obj=None):
            return False

      #readonly_fields=('experiment_session','recruitment_params', 'users', 'subjectText', 'messageText', '')
      
      search_fields = ['id','experiment_session__experiment__title',]
      #list_display = [']

class ExperimentSessionInvitationsInline(admin.TabularInline):
      '''
      experiment session day inline
      '''
      def has_add_permission(self, request, obj=None):
        return False

      def has_change_permission(self, request, obj=None):
        return False

      extra = 0  
      model = ExperimentSessionInvitations
      can_delete = False
      show_change_link = True
      fields=('mailResultSentCount','mailResultErrorText')

@admin.register(ExperimentSessions)
class ExperimentSessionsAdmin(admin.ModelAdmin):
      
      def render_change_form(self, request, context, *args, **kwargs):
         context['adminform'].form.fields['budget'].queryset = User.objects.filter(profile__type__id=1, profile__pi_eligible=True).order_by('last_name','first_name')
      
         return super(ExperimentSessionsAdmin, self).render_change_form(request, context, *args, **kwargs)
         
      def has_delete_permission(self, request, obj=None):
            return False
      
      def has_add_permission(self, request, obj=None):
            return False

      readonly_fields=('experiment', 'recruitment_params', 'creator')
      inlines = [ExperimentSessionDayInline, ExperimentSessionInvitationsInline]

      search_fields = ['id','experiment__title',]

class ExperimentInstitutionsInline(admin.TabularInline):
      '''
      experiment session inline
      '''
      def has_add_permission(self, request, obj=None):
        return False

      def has_change_permission(self, request, obj=None):
        return False

      extra = 0  
      model = ExperimentsInstitutions
      can_delete = False
      show_change_link = True

@admin.register(Experiments)
class ExperimentsAdmin(admin.ModelAdmin):
      def has_delete_permission(self, request, obj=None):
            return False
      
      def has_add_permission(self, request, obj=None):
            return False
      
      def get_form(self, request, obj=None, **kwargs):
            form = super().get_form(request, obj, **kwargs)

            form.base_fields['school'].widget.can_change_related = False
            form.base_fields['school'].widget.can_add_related = False

            form.base_fields['account_default'].widget.can_change_related = False
            form.base_fields['account_default'].widget.can_add_related = False

            form.base_fields['consent_form_default'].widget.can_change_related = False
            form.base_fields['consent_form_default'].widget.can_add_related = False

            form.base_fields['budget_default'].queryset = User.objects.filter(profile__type__id=1, profile__pi_eligible=True).order_by('last_name','first_name')
            form.base_fields['experiment_pi'].queryset = User.objects.filter(profile__type__id=1, profile__pi_eligible=True).order_by('last_name','first_name')

            return form
      
      def archive(self, request, queryset):

            updated_traits = queryset.update(archived=True)

            self.message_user(request, ngettext(
                  '%d experment was archived.',
                  '%d experiments were archived.',
                  updated_traits,
            ) % updated_traits, messages.SUCCESS)
      archive.short_description = "Archive selected experiments"

      @admin.display(description='Date Range')
      def date_range(self, obj):
        return obj.getDateRangeString()

      @admin.display(description='Last Run Date')
      def last_date_run(self, obj):
            experiment_session_day = main.models.ExperimentSessionDays.objects.filter(experiment_session__experiment=obj).order_by('-date').first()

            return experiment_session_day.date if experiment_session_day else None
      
      ordering = ['-timestamp']
      inlines = [ExperimentSessionInline, ExperimentInstitutionsInline]
      search_fields = ['id', 'title', 'experiment_manager',]
      readonly_fields = ('recruitment_params_default',)
      list_display = ['id', 'title', 'experiment_manager', 'archived', 'timestamp', 'last_date_run', 'date_range']
      actions = ['archive']
      list_filter = ['archived']

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
