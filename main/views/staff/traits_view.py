import csv
import json
import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.db.models import F, Value, CharField
from django.db.models.functions import Lower
from django.contrib.admin.views.decorators import staff_member_required
from django.views import View
from django.utils.decorators import method_decorator

from main.forms import traitReportForm
from main.decorators import user_is_staff

from main.models import Traits
from main.models import profile_trait
from main.models import profile
from main.models import help_docs

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

        logger = logging.getLogger(__name__)

        try:
            logger.info(request.path)
            helpText = help_docs.objects.annotate(rp = Value(request.path,output_field=CharField()))\
                                .filter(rp__icontains = F('path')).first().text
        except Exception  as e:   
            logger.info(f'{e}')
            helpText = "No help doc was found."

        return render(request, self.template_name,{"traitReportForm":traitReportForm(),
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

        #check for file upload
        try:
            f = request.FILES['file']
            return takeCSVUpload(f,u)
        except Exception  as e: 
            logger.info(f'traitsView no file upload: {e}')

        #no file to upload
        data = json.loads(request.body.decode('utf-8'))
        
        if data["action"] == "getReport":
            return getReport(data, u)
        elif data["action"] == "action2":
            pass
           
        return JsonResponse({"response" :  "fail"}, safe=False)    

#get CSV file users with specified traits
def getReport(data,u):

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

        active_only = data["active_only"]
        traits_list = form.cleaned_data['traits']

        t_list = profile_trait.objects.filter(trait__in = traits_list) \
                                      .select_related('my_profile__user__first_name',
                                                      'my_profile__user__last_name',
                                                      'my_profile__studentID',
                                                      'my_profile__user__is_active',
                                                      'my_profile__id',
                                                      'trait__name',
                                                      'trait__id') \
                                      .values('trait__name',
                                              'trait__id',
                                              'value',
                                              'my_profile__user__first_name',
                                              'my_profile__user__last_name',
                                              'my_profile__studentID',
                                              'my_profile__id') \
                                      .order_by(Lower('my_profile__user__last_name'),Lower('my_profile__user__first_name'))
        
        if active_only:
            t_list = t_list.filter(my_profile__user__is_active = True) \
                           .filter(my_profile__email_confirmed = 'yes')

        logger.info(t_list)

        u_list = {}

        traits_list_ids = traits_list.values_list('id',flat=True)
        
        
        for i in t_list:
            #setup empty list
            v=None

            if u_list.get(i['my_profile__id'],-1) == -1:
                u_list[i['my_profile__id']] = {"last_name" : i['my_profile__user__last_name'],
                                               "first_name" : i['my_profile__user__first_name'],
                                               "student_id" : i['my_profile__studentID'],
                                               "traits":{}}

                v = u_list.get(i['my_profile__id'])
            
                for j in traits_list_ids:
                    v["traits"][j] = None
            else:
                v = u_list.get(i['my_profile__id'])

            v["traits"][i['trait__id']] = i['value']
        

        logger.info(u_list)

        csv_response = HttpResponse(content_type='text/csv')
        csv_response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

        writer = csv.writer(csv_response)

        headerText = ['Student ID','Last Name','First Name']

        for i in traits_list:
            headerText.append(i)

        writer.writerow(headerText)

        for u_id in u_list:
            u = u_list.get(u_id)
            t=[]

            t.append(u['student_id'])
            t.append(u['last_name'])
            t.append(u['first_name'])

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
    v=""

    for chunk in f.chunks():
        v+=str(chunk.decode("utf-8-sig"))            
    
    v=v.splitlines()

    for i in range(len(v)):
        v[i] = v[i].split(',')

    logger.info(v)

    #check that data is in correct format
    if v[0][0] !="num" or v[0][1] !="chapmanid" or v[0][2] != "fullname":
        status = "fail"
        message = "Invalid Format: No num, chapmaid or fullname column."

    #create any new traits that do not exist
    if status!="fail":
        for i in v[0]:                
            if i != "num" and i != "chapmanid" and i != "fullname":
                t = Traits.objects.filter(name = i).first()

                if not t:
                    t_new = Traits()
                    t_new.name = i
                    t_new.save()

                    message += f"New trait created: {i}<br>"
    
    #store traits
    if status != "fail":
        for i in range(1,len(v)):

            r = v[i]

            p = profile.objects.filter(studentID__icontains = int(r[1]))

            if len(p) == 1:
                p = p.first()
                # try:
                for j in range(3,len(r)):
                    #find trait and profile 
                    t = Traits.objects.filter(name = v[0][j]).first()
                    pt = profile_trait.objects.filter(my_profile = p,trait=t).first()

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
                    
                message += f"Traits loaded for: <a href='/userInfo/{p.user.id}/'>{r[2]}</a><br>"

                # except Exception  as e: 
                #     status = "fail"
                #     message += f"Failed to load trait for:  {e}<br>"
            else:
                status = "fail"
                message += f"Subject not found: {r[2]}<br>"
    
    
    logger.info(f'Trait CSV upload result: {status} {message}')
    return JsonResponse({"response" : status,"message":message},safe=False)
