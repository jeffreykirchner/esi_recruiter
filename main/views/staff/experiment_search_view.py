
import json
import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models.functions import Lower
from django.db.models import Q, F, Value, CharField
from django.db.models import Count
from django.http import JsonResponse
from django.contrib.postgres.search import TrigramSimilarity
from django.views import View
from django.utils.decorators import method_decorator

from main.decorators import user_is_staff
from main.models import Experiments
from main.models import ExperimentSessionDays
from main.models import schools
from main.models import Accounts
from main.models import recruitment_parameters
from main.models import parameters
from main.models import Genders
from main.models import subject_types
from main.models import help_docs
from main.models import Invitation_email_templates    

class ExperimentSearch(View):
    '''
    experiment search view
    '''

    template_name = "staff/experiment_search.html"

    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logger = logging.getLogger(__name__)

        try:
            helpText = help_docs.objects.annotate(rp=Value(request.path, output_field=CharField()))\
                                        .filter(rp__icontains=F('path')).first().text

        except Exception  as e:   
             helpText = "No help doc was found."

        return render(request, self.template_name, {"helpText":helpText, "id":""})

    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__) 

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "searchExperiments":
            return searchExperiments(data)
        elif data["action"] == "getAllExperiments":
            return getAllExperiments(data)
        elif data["action"] == "getOpenExperiments":
            return getOpenExperiments(data)
        elif data["action"] == "createExperiment":
            return createExperiment(data)   
        elif data["action"] == "deleteExperiment":
            return deleteExperiment(data) 
        elif data["action"] == "getRecentExperiments":
            return getRecentExperiments(data)
           
        return JsonResponse({"status" :  "error"},safe=False)

#create experiment
def createExperiment(data):
    logger = logging.getLogger(__name__)
    logger.info("Create Experiment")
    logger.info(data)

    e = createExperimentBlank()

    return JsonResponse({"experiments" : [e.json_search()]},safe=False)

#create blank experiment
def createExperimentBlank():
    logger = logging.getLogger(__name__)
    logger.info("Create Blank Experiment")
    
    rp = recruitment_parameters()
    p = parameters.objects.first()

    #setup with initial genders selected
    g_list=list(Genders.objects.filter(initialValue = True))
    st_list = list(subject_types.objects.filter(initialValue = True))
    schools_list = list(schools.objects.filter(initialValue = True))

    #get invitation text from first template
    t = Invitation_email_templates.objects.filter(enabled=True)
    invitationText=""
    if t.count()>0:
        invitationText = t.first().body_text

    e = Experiments()
    e.school = schools.objects.first()
    e.account_default = Accounts.objects.first()
    e.recruitment_params_default = rp
    e.showUpFee = p.defaultShowUpFee
    e.invitationText = invitationText
    e.reminderText = p.reminderText

    rp.save()
    e.save()    

    rp.gender.set(g_list)
    rp.subject_type.set(st_list)
    rp.schools_include.set(schools_list)

    rp.save()

    return e

#serach for an experiment
def searchExperiments(data):
    logger = logging.getLogger(__name__)
    logger.info("Search Experiments")
    logger.info(data)

    e_list_json = lookup(data["searchInfo"])

    return JsonResponse({"experiments" : e_list_json},safe=False)

#delete selected experiment
def deleteExperiment(data):
    logger = logging.getLogger(__name__)
    logger.info("Delete Experiment")
    logger.info(data)

    status = ""

    id = data["id"]

    e = Experiments.objects.get(id=id)

    title = e.title

    if e.allowDelete():
        e.delete()
        status="success"
    else:
        status="fail"

    return JsonResponse({"status" : status,
                         "title":title,
                         "experiments_recent" : getRecentExperimentsList()},safe=False)

#get a list of all experiments
def getAllExperiments(data):
    logger = logging.getLogger(__name__)
    logger.info("Get All Experiments")
    logger.info(data)

    e_list=Experiments.objects.order_by(Lower("title"))         
    
    e_list_json = [e.json_search() for e in e_list]

    return JsonResponse({"experiments" : e_list_json},safe=False)

#get a list of all experiments
def getOpenExperiments(data):
    logger = logging.getLogger(__name__)
    logger.info("Get Open Experiments")
    logger.info(data)

    esd_open = ExperimentSessionDays.objects.annotate(user_count = Count('ESDU_b'))\
                                      .filter(complete=False)\
                                      .values_list('experiment_session__experiment__id',flat=True)

    # logger.info(list(esd_open))

    e_list=Experiments.objects.filter(id__in=esd_open)\
                              .distinct()\
                              .order_by(Lower("title"))
    
    e_list_json = [e.json_search() for e in e_list]

    return JsonResponse({"experiments" : e_list_json},safe=False)

#get list of most recently updated experiments
def getRecentExperiments(data):
    logger = logging.getLogger(__name__)
    logger.info("Get Recent Experiments")
    logger.info(data)

    return JsonResponse({"experiments_recent" : getRecentExperimentsList()},safe=False)

def getRecentExperimentsList():
    logger = logging.getLogger(__name__)
    logger.info("Get Recent Experiments List")

    e_list = Experiments.objects.order_by('-updated')[:10]

    return [e.json_search() for e in e_list]


#search for users that back search criterion
def lookup(value):
    logger = logging.getLogger(__name__)
    logger.info(f"Experiment Lookup: {value}")
   
    # e_list = Experiments.objects.order_by(Lower('title')) \
    #                   .filter(Q(title__icontains = value) |
    #                           Q(experiment_manager__icontains = value) |
    #                           Q(notes__icontains = value))

    value = value.strip()

    e_list = Experiments.objects.annotate(title_similarity=TrigramSimilarity('title', value)) \
                        .annotate(experiment_manager_similarity=TrigramSimilarity('experiment_manager', value)) \
                        .annotate(notes_similarity=TrigramSimilarity('notes', value)) \
                        .annotate(similarity_total=F('title_similarity') +
                                                   F('experiment_manager_similarity') +
                                                   F('notes_similarity')) \
                        .filter(Q(title_similarity__gte=0.3) |
                                Q(experiment_manager_similarity__gte=0.3) |
                                Q(notes_similarity__gte=0.3))\
                        .order_by('-similarity_total')


    e_list_json = [e.json_search() for e in e_list]

    return e_list_json