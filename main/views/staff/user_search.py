from datetime import datetime, timedelta, timezone
from functools import reduce

import json
import logging
import uuid
import operator

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import CharField, Q, F, Value as V
from django.db.models.functions import Lower
from django.contrib.postgres.search import TrigramSimilarity
from django.views import View
from django.utils.decorators import method_decorator
from django.conf import settings

from main.decorators import user_is_staff

from main.models import Parameters
from main.models import HelpDocs
from main.models import profile

from main.globals import send_mass_email_service
from main.globals import get_now_show_blocks
from main.globals import todays_date

class UserSearch(View):
    '''
    user search view
    '''

    template_name = "staff/user_search.html"

    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logger = logging.getLogger(__name__)
        
        try:
            helpText = HelpDocs.objects.annotate(rp = V(request.path,output_field=CharField()))\
                                    .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
             helpText = "No help doc was found."

        activeCount = User.objects.filter(is_active = True,
                                          profile__type__id = 2,
                                          profile__email_confirmed = 'yes',
                                          profile__paused = False).count()
        
        activeCountRecent = User.objects.filter(last_login__gte = todays_date() - timedelta(days=90),
                                               profile__type__id = 2,
                                               profile__email_confirmed = 'yes',
                                               profile__paused = False).count()

        return render(request, self.template_name, {"activeCount" : activeCount,
                                                    "activeCountRecent" : activeCountRecent,
                                                    "helpText":helpText})
    
    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__) 

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "getUsers":
            return getUsers(request, data)
        elif data["action"] == "getBlackBalls":
            return getBlackBalls(request, data)
        elif data["action"] == "getNoShows":
            return getNoShows(request, data)
        elif data["action"] == "sendEmail":
            return sendEmail(request, data)
        elif data["action"] == "sendInternational":
            return sendInternational(request, data)

#mark the submitted subjects as international
def sendInternational(request, data):
    logger = logging.getLogger(__name__)
    logger.info(f"Set subjects to International: {data}")

    error_message = ""
    text = data["subject_list"]

    v=text.splitlines()
    student_id_list = []

    for i in range(len(v)):
        try:
            student_id_list.append(int(v[i]))        
        except ValueError:
            error_message += f'Invalid ID: {v[i]}<br>'

    logger.info(f"sendInternational list: {student_id_list}")

    if len(student_id_list) == 0:
         error_message = "No users found"
         logger.info(f"sendInternational error: {error_message}")
         return JsonResponse({"users" : {},
                              "errorMessage":error_message},safe=False)

    clauses = (Q(studentID__icontains=p) for p in student_id_list)
    query = reduce(operator.or_, clauses)
    profiles = profile.objects.filter(query)
    profiles.update(international_student=True)

    users = User.objects.filter(id__in=profiles.values_list("user__id", flat=True))
    users = users.order_by(Lower('last_name'),Lower('first_name'))\
                 .values("id",
                        "first_name",
                        "last_name",
                        "email",
                        "profile__studentID",
                        "profile__type__name",
                        "profile__public_id",
                        "is_active",
                        "profile__subject_type__name",
                        "profile__blackballed")

    u_list = list(users)

    return JsonResponse({"users" : json.dumps(u_list,cls=DjangoJSONEncoder),
                         "errorMessage":error_message},safe=False)

#send an email to active users
def sendEmail(request, data):
    logger = logging.getLogger(__name__)
    logger.info(f"Send message to all active users {data}")

    if request.user.is_staff:

        params = Parameters.objects.first()

        subjectText = data["subject"]
        messageText = data["text"]

        users_list = User.objects.filter(is_active=True,
                                         profile__email_confirmed='yes',
                                         profile__paused = False,
                                         profile__type__id=2)

        #debug
        if settings.DEBUG:
            users_list = users_list[:1]
        
        messageText = messageText.replace("[contact email]",params.labManager.email)

        user_list = []
        for user in users_list:
            user_list.append({"email":user.email,
                              "variables": [{"name":"first name","text":user.first_name},
                                            ]})
        
        memo = f'Send message to all active users'

        mail_result = send_mass_email_service(user_list, subjectText, messageText, messageText, memo, len(users_list) *2)

        #logger.info(emailList)
    else:
        logger.info("Send message to all active users error, not staff user : user " + str(request.user.id))
        mail_result = {"mail_count":0, "error_message":"You are not an elevated user."}

    return JsonResponse({"mailResult":mail_result}, safe=False)

#get a list of no show violators
def getNoShows(request, data):
    logger = logging.getLogger(__name__)
    logger.info("Get no show blocks")
    logger.info(data)

    p = Parameters.objects.first()
    d = datetime.now(timezone.utc) - timedelta(days=p.noShowCutoffWindow)

    errorMessage = ""
    active_only = data["activeOnly"] 

    users = get_now_show_blocks()
    users = users.order_by(Lower('last_name'),Lower('first_name'))\
                 .values("id",
                         "first_name",
                         "last_name",
                         "email",
                         "profile__studentID",
                         "profile__type__name",
                         "profile__public_id",
                         "is_active",
                         "profile__subject_type__name",
                         "profile__blackballed")

    # users=User.objects.order_by(Lower('last_name'),Lower('first_name')) \
    #             .filter(Q(ESDU__confirmed = True) &
    #                 Q(ESDU__attended = False) &
    #                 Q(ESDU__bumped = False) & 
    #                 Q(ESDU__experiment_session_day__experiment_session__canceled = False) &
    #                 Q(ESDU__experiment_session_day__date__gte = d))\
    #             .annotate(noShows = Count('id'))\
    #             .filter(noShows__gte = p.noShowCutoff)\
    #             .values("id","first_name","last_name","email","profile__studentID","profile__type__name","is_active","profile__blackballed")

    #logger.info(users.query)

    if active_only:
        users = users.filter(is_active = True, profile__paused = False)

    u_list = list(users)

    return JsonResponse({"users" :  json.dumps(u_list,cls=DjangoJSONEncoder),"errorMessage":errorMessage},safe=False)

#get a list of all active black ball users
def getBlackBalls(request,data):
    logger = logging.getLogger(__name__)
    logger.info("Black Balls")
    logger.info(data)

    errorMessage=""
    active_only = data["activeOnly"] 

    users=User.objects.order_by(Lower('last_name'),Lower('first_name')) \
                .filter(profile__blackballed=True) \
                .select_related('profile') \
                .values("id",
                        "first_name",
                        "last_name",
                        "email",
                        "profile__studentID",
                        "profile__type__name",
                        "profile__public_id",
                        "is_active",
                        "profile__subject_type__name",
                        "profile__blackballed")
    
    if active_only:
        users = users.filter(is_active = True, profile__paused = False)

    u_list = list(users)

    return JsonResponse({"users" :  json.dumps(u_list,cls=DjangoJSONEncoder),"errorMessage":errorMessage},safe=False)

#return list of users based on search criterion
def getUsers(request, data):
    logger = logging.getLogger(__name__)
    logger.info("User Search")
    logger.info(data)

    #request.session['userSearchTerm'] = data["searchInfo"]            
    active_only = data["activeOnly"] 

    users = lookup(data["searchInfo"], False, active_only)            

    errorMessage = ""

    if(len(users) >= 1000):
        errorMessage = "Narrow your search"
        users = []          

    return JsonResponse({"users" : json.dumps(users, cls=DjangoJSONEncoder), 
                         "errorMessage":errorMessage},safe=False)

#search for users that back search criterion
def lookup(value, return_json, active_only, subjects_only=False):
    logger = logging.getLogger(__name__)
    logger.info("User Lookup")
    logger.info(value)

    value = value.strip()

    is_uuid = True
    try:
        uuid.UUID(value)        
    except ValueError:
        is_uuid = False

    users = User.objects.annotate(first_name_similarity=TrigramSimilarity('first_name', value)) \
                        .annotate(last_name_similarity=TrigramSimilarity('last_name', value)) \
                        .annotate(email_similarity=TrigramSimilarity('email', value)) \
                        .annotate(profile_studentID_similarity=TrigramSimilarity('profile__studentID', value)) \
                        .annotate(profile_type__name_similarity=TrigramSimilarity('profile__type__name', value)) \
                        .annotate(profile__subject_type__name_similarity=TrigramSimilarity('profile__subject_type__name', value)) \
                        .annotate(similarity_total=F('first_name_similarity') +
                                                   F('last_name_similarity') +
                                                   F('email_similarity') +
                                                   F('profile_studentID_similarity') +
                                                   F('profile__subject_type__name_similarity') +
                                                   F('profile_type__name_similarity')) \
                        .filter(Q(first_name_similarity__gte=0.3) |
                                Q(last_name_similarity__gte=0.3) |
                                Q(email_similarity__gte=0.3) |
                                Q(profile_studentID_similarity__gte=0.3) |
                                Q(profile__subject_type__name_similarity__gte=0.3) |
                                Q(profile_type__name_similarity__gte=0.3) |
                                Q(id=value if value.isnumeric() else None) |
                                Q(profile__public_id=value if is_uuid else None))\
                        .select_related('profile')\
                        .values("id",
                                "first_name",
                                "last_name",
                                "email",
                                "profile__studentID",
                                "profile__type__name",
                                "profile__public_id",
                                "is_active",
                                "profile__subject_type__name",
                                "profile__blackballed") \
                        .order_by('-similarity_total')

    if active_only:
        users = users.filter(is_active=True, 
                             profile__paused = False, 
                             profile__disabled=False,
                             profile__email_confirmed='yes')
    
    if subjects_only:
        users = users.filter(profile__type__id=2)

    u_list = list(users[:100])

    logger.info(str(len(u_list)) + " results found.")

    for u in u_list:
        u['first_name'] = u['first_name'].capitalize()
        u['last_name'] = u['last_name'].capitalize()

    if return_json:
        #print(json.dumps(list(users),cls=DjangoJSONEncoder))
        return json.dumps(u_list, cls=DjangoJSONEncoder)
    else:
        return u_list
