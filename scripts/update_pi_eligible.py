from main.models import profile

profile.objects.filter(type__name="staff", user__is_active=True).update(pi_eligible=True)
