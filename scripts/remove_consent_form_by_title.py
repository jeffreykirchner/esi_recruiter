from django.db.models import Q

from main.models import ConsentForm
from main.models import experiments
from main.models import experiment_session_day_users
from main.models import experiment_session_days
from main.models import experiment_sessions
from main.models import ProfileConsentForm

print("Enter experiment title(ex: Fitbit Study: Orientation Meeting):")
experiment_name = input() #"Blanket 2021"
experiment = experiments.objects.get(title=experiment_name)

experiment.ES.update(consent_form=None)

#print(f"Profile consent forms created: {objs}")