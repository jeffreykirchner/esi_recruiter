import json
import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import CharField, F, Value as V
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.views import View
from django.utils.decorators import method_decorator

from main.models import Parameters
from main.models import HelpDocs
from main.models import ConsentForm
from main.models import ProfileConsentForm
from main.models import ExperimentSessions
from main.models import UmbrellaConsentForm

from main.decorators import user_is_subject
from main.decorators import email_confirmed

import  main

class SubjectConsent(View):
    '''
    subject consent form
    '''

    template_name = "subject/consent_form.html"

    @method_decorator(login_required)
    @method_decorator(user_is_subject)
    @method_decorator(email_confirmed)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logger = logging.getLogger(__name__)

        u = request.user
        id = kwargs['id']
        consent_type = kwargs['type']
        view_mode = kwargs['view_mode']
        p = Parameters.objects.first()

        labManager = p.labManager

        try:
            helpText = HelpDocs.objects.annotate(rp = V(request.path,output_field=CharField()))\
                                        .filter(rp__icontains = F('path')).first().text

        except Exception  as e:   
            helpText = "No help doc was found."

        try:
            if consent_type == 'session':

                subject_session_list = u.ESDU.values_list('experiment_session_day__experiment_session__id',flat=True)
                session = ExperimentSessions.objects.filter(id__in=subject_session_list).filter(id=id)

                # logger.info(subject_session_list)
                # logger.info(session)

                if not session:
                    raise Http404('Form Not Found')

                consent_form = session.first().consent_form 
                
            elif consent_type == 'policy':
                umbrella_consent_form = UmbrellaConsentForm.objects.filter(id=id)

                if not umbrella_consent_form:
                    raise Http404('Form Not Found')
                
                consent_form = umbrella_consent_form.first().consent_form 
            else:
                raise Http404('Form Not Found')

            consent_form_subject = None
            
            if view_mode == "sign" and consent_type == 'session':
                if u.profile.check_for_consent_attended(consent_form):
                    consent_form_subject = ProfileConsentForm.objects.filter(consent_form=consent_form, my_profile=u.profile).last()
            else:
                consent_form_subject = ProfileConsentForm.objects.filter(consent_form=consent_form, my_profile=u.profile).last()

        except ObjectDoesNotExist :
            raise Http404('Form Not Found')
    

        return render(request, 
                      self.template_name, 
                      {"labManager":labManager,
                       "consent_form_json": json.dumps(consent_form.json(),cls=DjangoJSONEncoder) if consent_form else json.dumps(None,cls=DjangoJSONEncoder),
                       "consent_form_subject_json": json.dumps(consent_form_subject.json(),cls=DjangoJSONEncoder) if consent_form_subject else json.dumps(None,cls=DjangoJSONEncoder),
                       "helpText":helpText})

    @method_decorator(login_required)
    @method_decorator(user_is_subject)
    @method_decorator(email_confirmed)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__) 

        u = request.user
        id = kwargs['id']
        consent_type = kwargs['type']
        session = None
        
        try:
            if consent_type == 'session':
                subject_session_list = u.ESDU.values_list('experiment_session_day__experiment_session__id',flat=True)
                session = ExperimentSessions.objects.filter(id__in=subject_session_list).get(id=id)

                if not session:
                    logger.error("SubjectConsent: Session not found")
                    return JsonResponse({"response" :  "fail"},safe=False)  

            elif consent_type == 'policy':
                umbrella_consent_form = UmbrellaConsentForm.objects.filter(id=id)

                if not umbrella_consent_form:
                    logger.error("SubjectConsent: Policy not found")
                    return JsonResponse({"response" :  "fail"},safe=False)  
            else:
                logger.error("SubjectConsent: Invaid consent type")
                return JsonResponse({"response" :  "fail"},safe=False)

        except ObjectDoesNotExist :
            logger.error("SubjectConsent: Object not found")
            return JsonResponse({"response" :  "fail"},safe=False)  

        data = json.loads(request.body.decode('utf-8'))

        if data["action"] == "acceptConsentForm":
            return acceptConsentForm(data, u, session, consent_type)
            
        return JsonResponse({"response" :  "fail"},safe=False)

#subject accepts consent form
def acceptConsentForm(data, u, session, consent_type):
    '''
    Subject accepts consent form
    
    :param data: Form data{} empty
    :type data: dict

    :param u: Subject User
    :type u: django.contrib.auth.models.User

    :param session: Experiment Session
    :type u: Experiment Session model
    '''

    logger = logging.getLogger(__name__)
    logger.info(f"Accept consent form: user {u}, session : {session}, data {data}")    

    failed = False

    try:

        consent_form = ConsentForm.objects.get(id=data["consent_form_id"])
        signature_points = data["consent_form_signature"]
        singnature_resolution = data["consent_form_signature_resolution"]

        if consent_type=="session" and  session.consent_form != consent_form:
            logger.warning("consent form does not match")
            failed = True

        if not failed:
            profile_consent_form = ProfileConsentForm(my_profile=u.profile, 
                                                    consent_form=consent_form, 
                                                    signature_points=signature_points,
                                                    singnature_resolution=singnature_resolution)
            profile_consent_form.save()

            main.views.acceptInvitation({"id":session.id}, u)

    except Exception  as e:
        logger.warning("accept consent form error")             
        logger.warning("User: " + str(u.id))    
        logger.warning(e)
        failed = True

    return JsonResponse({"failed":failed,
                         "consent_form_subject_json": json.dumps(profile_consent_form.json(),cls=DjangoJSONEncoder) if profile_consent_form else json.dumps(None,cls=DjangoJSONEncoder),
                         }, safe=False)
