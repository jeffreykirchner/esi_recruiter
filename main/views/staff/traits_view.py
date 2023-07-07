import csv
import json
import logging

from io import StringIO

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.db.models import F, Value, CharField
from django.db.models.functions import Lower
from django.contrib.admin.views.decorators import staff_member_required
from django.views import View
from django.utils.decorators import method_decorator
from django.core.serializers.json import DjangoJSONEncoder

from main.forms import traitReportForm
from main.decorators import user_is_staff

from main.models import Traits
from main.models import profile_trait
from main.models import profile
from main.models import help_docs
from main.models import experiment_session_day_users
from main.models import experiment_session_days

class TraitsView(View):
    '''
    Traits upload and reporting
    '''

    template_name = "staff/traits.html"

    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    @method_decorator(staff_member_required)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        session_day_id = request.GET.get('SESSION_DAY_ID', None)
        session_day = None

        if session_day_id:
            result = experiment_session_days.objects.filter(id=session_day_id).values('id','experiment_session__experiment__title')
            if result:
                session_day = result.first()

        logger = logging.getLogger(__name__)

        try:
            logger.info(request.path)
            helpText = help_docs.objects.annotate(rp = Value(request.path,output_field=CharField()))\
                                .filter(rp__icontains = F('path')).first().text
        except Exception  as e:   
            logger.info(f'{e}')
            helpText = "No help doc was found."

        return render(request, self.template_name,{"traitReportForm":traitReportForm(),
                                                   "session_day" : json.dumps(session_day,cls=DjangoJSONEncoder),
                                                   "helpText":helpText})

    
    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    @method_decorator(staff_member_required)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__) 

        u = request.user

        # debug
        # f = request.FILES['file']
        # return takeCSVUpload(f,u)
        #check for file upload
        try:
            f = request.FILES['file']
            return takeCSVUpload(f,u)
        except Exception  as e: 
            logger.info(f'traitsView no file upload: {e}')
            
        #no file to upload
        data = json.loads(request.body.decode('utf-8'))

        session_day = data["session_day"]
        
        if data["action"] == "getReport":
            return getReport(data, u, session_day.get('id') if session_day else None)
        elif data["action"] == "action2":
            pass
           
        return JsonResponse({"response" :  "fail"}, safe=False)    

#get CSV file users with specified traits
def getReport(data, u, session_day_id):

    logger = logging.getLogger(__name__)
    logger.info("Get Trait Report CSV")
    logger.info(data)

    form_data_dict = {}
    traitsList=[]

    for field in data["formData"]:
        if field["name"] == "traits":
            traitsList.append(field["value"])
        else:
            form_data_dict[field["name"]] = field["value"]
    
    form_data_dict["traits"] = traitsList

    logger.info(form_data_dict)
    
    form = traitReportForm(form_data_dict)

    if form.is_valid():

        #optionally only pull data for subjects from this session day
        session_day = None

        if session_day_id:
            result = experiment_session_days.objects.filter(id=session_day_id)
            if result:
                session_day = result.first()

        active_only = data["active_only"]
        traits_list = form.cleaned_data['traits']

        #get list of valid profiles
        profiles = profile.objects.filter(email_confirmed = 'yes')\
                                  .filter(type = 2)\
                                  .select_related('user', 'major', 'gender', 'subject_type')\
                                  .order_by(Lower('user__last_name'),Lower('user__first_name'))
        
        #if session day provided only return data from that session day
        if session_day:
            esdu_list = session_day.ESDU_b.filter(attended=True) \
                                        .values_list('user__profile__id', flat=True)
            profiles = profiles.filter(id__in=esdu_list)

        if active_only:
            profiles = profiles.filter(paused = False)
        
        #id list of needed profiles
        profiles_ids = profiles.values_list('id', flat=True)

        #dict of profile values
        profiles = profiles.values('user__first_name',
                                   'user__last_name',
                                   'studentID',
                                   'paused',
                                   'user__id',
                                   'public_id',
                                   'major__name',
                                   'gender__name',
                                   'subject_type__name',
                                   'id') \
        
        #generate list of experiments attended by subject
        attended_list_a = experiment_session_day_users.objects.select_related('user__profile', 
                                                                              'experiment_session_day__experiment_session__experiment')\
                                                              .filter(attended=True)\
                                                              .filter(user__profile__id__in=profiles_ids)\
                                                              .values('user__profile__id',
                                                                      'experiment_session_day__experiment_session__experiment__id')

        attended_list_b = {}
        for i in attended_list_a:
            if not attended_list_b.get(i['user__profile__id'], None):
                attended_list_b[i['user__profile__id']] = {"count":set()}
            
            attended_list_b[i['user__profile__id']]["count"].add(i['experiment_session_day__experiment_session__experiment__id'])


        #generate list of traits for each subject
        t_list = profile_trait.objects.filter(trait__in = traits_list) \
                                      .filter(my_profile__id__in = profiles_ids) \
                                      .select_related('my_profile__id',
                                                      'my_profile__paused'
                                                      'trait__name',
                                                      'trait__id') \
                                      .values('trait__name',
                                              'trait__id',
                                              'value',
                                              'my_profile__id') \
            
        #logger.info(t_list)

        traits_list_ids = traits_list.values_list('id',flat=True)

        traits_base = {}
        
        for j in traits_list_ids:
            traits_base[j] = None

        u_list = {}

        for i in profiles:
            v=None

            u_list[i['id']] = {"last_name" : i['user__last_name'],
                               "first_name" : i['user__first_name'],
                               "student_id" : i['studentID'],
                               "recruiter_id" : i['user__id'],
                               "public_id" : i['public_id'],
                               "major" : i['major__name'],
                               "gender" : i['gender__name'],
                               "subject_type" : i['subject_type__name'],
                               "attended_count" : len(attended_list_b[i['id']]["count"]) if attended_list_b.get(i['id'], None) else 0,
                               "traits": traits_base.copy()}            
            
        for i in t_list:
            #setup empty list
            v = u_list.get(i['my_profile__id'])

            v["traits"][i['trait__id']] = i['value']
        

        #logger.info(u_list)

        csv_response = HttpResponse(content_type='text/csv')
        csv_response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

        writer = csv.writer(csv_response)

        # trait names
        headerText = ['Recruiter ID', 'Student ID','Public ID', 'Last Name', 'First Name', 'Experiments Attended', 'Major', 'Gender Identity', 'Enrollment']

        for i in traits_list:
            headerText.append(i.name)

        writer.writerow(headerText)

        #trait descriptions
        headerText = ['', '','', '', '', '', 'Sign-up', 'Sign-up', 'Sign-up']

        for i in traits_list:
            headerText.append(i.description)

        writer.writerow(headerText)

        for u_id in u_list:
            u = u_list.get(u_id)
            t=[]

            t.append(u['recruiter_id'])
            t.append(u['student_id'])
            t.append(u['public_id'])
            t.append(u['last_name'])
            t.append(u['first_name'])
            t.append(u['attended_count'])
            t.append(u['major'])
            t.append(u['gender'])
            t.append(u['subject_type'])

            for i in traits_list:
                t.append(u['traits'][i.id])

            writer.writerow(t)

        return csv_response
    else:
        logger.info("invalid trait report form")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

#take CSV file upload and store traits from it
def takeCSVUpload(f,u):
    logger = logging.getLogger(__name__) 
    logger.info("Take trait CSV upload")

    status = "success"
    message = ""

    logger.info(f"File to be uploaded {f}")

    #format incoming data
    # v=""

    # for chunk in f.chunks():
    #     v += str(chunk.decode("utf-8-sig"))            
    
    # v=v.splitlines()

    # for i in range(len(v)):
    #     #v[i] = v[i].split(',')
    #     v[i] = list(csv.reader(v[i]))

    
    file = f.read().decode('utf-8')
    csv_data = csv.reader(StringIO(file), delimiter=',')
    v = list(csv_data)

    #v = list(reader)

    #print(data)

    logger.info(v)

    #check that data is in correct format
    if v[0][0] != "student_id" and v[0][0] != "recruiter_id" and v[0][0] != "public_id":
        status = "fail"
        message = "Invalid Format: First column must be either recruiter_id, student_id or public_id"

    #create any new traits that do not exist
    if status!="fail":
        for i in range(0, len(v[0])):             
            trait_name = v[0][i]
            trait_description = v[1][i] 

            if trait_name != "student_id" and trait_name != "recruiter_id" and trait_name != "public_id":
                t = Traits.objects.filter(name = trait_name).first()

                if not t:
                    t_new = Traits()
                    t_new.name = trait_name
                    t_new.description = trait_description
                    t_new.save()

                    message += f"New trait created: {trait_name}<br>"
    
    #store traits
    if status != "fail":
        for i in range(2,len(v)):

            r = v[i]

            if v[0][0] == "student_id":
                p = profile.objects.filter(studentID__icontains = int(r[0]))
            elif v[0][0] == "recruiter_id":
                p = profile.objects.filter(user__id = int(r[0]))
            else:
                p = profile.objects.filter(public_id = r[0])

            if len(p) == 1:
                p = p.first()
                # try:
                for j in range(1,len(r)):
                    #find trait and profile 
                    t = Traits.objects.filter(name = v[0][j]).first()
                    pt = profile_trait.objects.filter(my_profile = p,trait=t).first()

                    if r[j]:
                        if pt:
                            #profile trait exists, update it 
                            pt.value = r[j]
                            pt.save()
                        else:
                            #profile trait does not exist, create a new one
                            pt = profile_trait()
                            pt.my_profile = p
                            pt.trait = t
                            pt.value = r[j]
                            pt.save()
                    
                message += f"Traits loaded for: <a href='/userInfo/{p.user.id}/'>{p.user.last_name}, {p.user.first_name}</a><br>"

                # except Exception  as e: 
                #     status = "fail"
                #     message += f"Failed to load trait for:  {e}<br>"
            else:
                status = "fail"
                message += f"Subject not found: {r[2]}<br>"
    
    
    logger.info(f'Trait CSV upload result: {status} {message}')
    return JsonResponse({"response" : status,"message":message},safe=False)
