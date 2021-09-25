from datetime import datetime
from datetime import timedelta
from datetime import timezone

from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models import Count

from main.models import parameters

def get_now_show_blocks():
    '''
    return a query set of users currently under the now show block restriction
    '''
    p = parameters.objects.first()
    d = datetime.now(timezone.utc) - timedelta(days=p.noShowCutoffWindow)

    user_qs = User.objects.filter(Q(ESDU__confirmed = True) &
                                  Q(ESDU__attended = False) &
                                  Q(ESDU__bumped = False) & 
                                  Q(ESDU__experiment_session_day__experiment_session__canceled = False) &
                                  Q(ESDU__experiment_session_day__complete = True) &
                                  Q(ESDU__experiment_session_day__date__gte = d))\
                  .annotate(no_show_count = Count('id'))\
                  .filter(no_show_count__gte = p.noShowCutoff)

    return user_qs