from django.db.models import Q

from main.models import ConsentForm
from main.models import experiment_session_day_users
from main.models import experiment_session_days
from main.models import experiment_sessions
from main.models import ProfileConsentForm

print("Enter consent form title (ex: Blanket 2021-22):")
consent_form_name = input() #"Blanket 2021"
consent_form = ConsentForm.objects.get(name=consent_form_name)

print("Enter session numbers, space separated (ex: 3344 7789):")
sessions_input = input() #"2021-07-06"

sessions_input = sessions_input.split(' ')

session_list = experiment_sessions.objects.filter(id__in=sessions_input)

esd = experiment_session_days.objects.filter(experiment_session__in=session_list)

es_list = esd.values_list("experiment_session__id", flat=True)

#add consent forms to subjects
profiles = experiment_session_day_users.objects.filter(experiment_session_day__in=esd) \
                                               .filter(Q(attended=True) | Q(bumped=True)) \
                                               .values_list("user__profile__id", flat=True)

objs = ProfileConsentForm.objects.bulk_create([ProfileConsentForm(my_profile_id=p, consent_form=consent_form) for p in profiles],
                                              ignore_conflicts=True)

#print(f"Profile consent forms created: {objs}")