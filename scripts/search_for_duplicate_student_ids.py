from main.models import profile
from main.models import Schools

vaild_email_filters =[]

chapman_school = Schools.objects.get(id=1)

for email_filter in chapman_school.email_filter.all():
    vaild_email_filters.append(email_filter)

ids = {}

profiles = profile.objects.filter(paused=False) \
                          .filter(type__id=2) \
                          .filter(email_filter__in=vaild_email_filters)

for p in profiles:
    if p.studentID.isdigit():
        if not ids.get(int(p.studentID), False):
            ids[int(p.studentID)] = {"count" : 1, "profile" : p}
        else:
            ids[int(p.studentID)]["count"] += 1
    

for id in ids:
    if ids[id]["count"] > 1:
        print(f"Student ID: {id} has {ids[id]['count']} profiles")
                
