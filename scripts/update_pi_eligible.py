from main.models import profile

profile.objects.filter(type__name="staff").update(pi_eligible=True)
