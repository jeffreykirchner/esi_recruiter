from django.db.models import Q

from main.models import ConsentForm
from main.models import experiments
from main.models import experiment_session_day_users
from main.models import experiment_session_days
from main.models import experiment_sessions
from main.models import ProfileConsentForm

print("Updating fitbit payment consent forms...")

payments = experiments.objects.get(title="Fitbit Study: Payment")
sessions = experiments.objects.get(title="Fitbit Study: Orientation Meeting")

for i in payments.ES.all():
    esd = i.ESD.first()

    
    u = esd.ESDU_b.first()
    if u:
        u = u.user.id

        print(f"Updating Payment: {i}, {u}")

        for j in sessions.ES.all().prefetch_related('ESD'):        
            u_list = j.ESD.first().ESDU_b.filter(attended=True).values_list('user__id', flat=True)
            print(f"Search Session: {j}, {u_list}")
            if u in u_list:
                print(f"User found Payment: {i}")
                i.consent_form=j.consent_form
                i.save()
                break



