from django.db.models import Q

from main.models import ConsentForm
from main.models import experiment_session_day_users
from main.models import experiment_session_days
from main.models import experiment_sessions
from main.models import ProfileConsentForm
from main.models import experiments

print("Enter consent form title (ex: Blanket 2021-22):")
consent_form_name = input() #"Blanket 2021"
consent_form = ConsentForm.objects.get(name=consent_form_name)

print("Enter the experiment number (ex: 3344):")
experiment_input = input() #"2021-07-06"

e = experiments.objects.get(id=experiment_input)
e.consent_form_default=consent_form
e.save()
e.ES.update(consent_form=consent_form)

esd = experiment_session_days.objects.filter(experiment_session__in=e.ES.all())

#add consent forms to subjects
profiles = experiment_session_day_users.objects.filter(experiment_session_day__in=esd) \
                                               .filter(Q(attended=True) | Q(bumped=True)) \
                                               .values_list("user__profile__id", flat=True)

objs = ProfileConsentForm.objects.bulk_create([ProfileConsentForm(my_profile_id=p, consent_form=consent_form) for p in profiles],
                                              ignore_conflicts=True)

#print(f"Profile consent forms created: {objs}")