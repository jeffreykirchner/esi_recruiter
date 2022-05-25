from main.models import ConsentForm
from main.models import experiment_session_day_users
from main.models import experiment_session_days
from main.models import experiment_sessions
from main.models import ProfileConsentForm

#Blanket 2022
print("Enter consent form title (ex: Blanket 2021-22):")
consent_form_name = input() #"Blanket 2021"
consent_form = ConsentForm.objects.get(name=consent_form_name)

print("Enter Start Date Range (ex: yyyy-mm-dd):")
#2021-07-06
begin_date_range = input() #"2021-07-06"

print("Enter End Date Range (ex: yyyy-mm-dd):")
#2022-07-05
end_date_range = input() #"2022-07-05"

#add consent forms to sessions
esd = experiment_session_days.objects.filter(date__gte=begin_date_range).filter(date__lte=end_date_range)

es_list = esd.values_list("experiment_session__id", flat=True)

es = experiment_sessions.objects.filter(id__in=es_list)
es.update(consent_form=consent_form)

#print(f"Sessions updated: {es}")

#add consent forms to subjects
profiles = experiment_session_day_users.objects.filter(experiment_session_day__in=esd) \
                                               .filter(confirmed=True) \
                                               .values_list("user__profile__id", flat=True)

objs = ProfileConsentForm.objects.bulk_create([ProfileConsentForm(my_profile_id=p, consent_form=consent_form) for p in profiles],
                                              ignore_conflicts=True)

#print(f"Profile consent forms created: {objs}")

exit()