import json
import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from main.decorators import user_is_staff
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.generic.detail import SingleObjectMixin

from django.db.models import CharField, F, Value as V

from main.models import ProfileNote
from main.models import HelpDocs

from main.globals import get_now_show_blocks

from main.forms import EditSubjectForm

class UserInfo(SingleObjectMixin, View):
    '''
    user information view
    '''

    template_name = "staff/user_info.html"
    model = User

    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def get(self, request, *args, **kwargs):
        '''
        handle get requests
        '''

        logger = logging.getLogger(__name__)

        try:
            helpText = HelpDocs.objects.annotate(rp=V(request.path,output_field=CharField()))\
                                        .filter(rp__icontains=F('path')).first().text

        except Exception  as e:   
             helpText = "No help doc was found."

        u = self.get_object()

        edit_subject_form = EditSubjectForm()

        return render(request, self.template_name, {"u":u,
                                                    "id":u.id,
                                                    "now_show_block" :  True if u in get_now_show_blocks() else False,
                                                    "helpText":helpText,
                                                    "edit_subject_form":edit_subject_form,
                                                    "experiments":u.ESDU.all() })
    
    @method_decorator(login_required)
    @method_decorator(user_is_staff)
    def post(self, request, *args, **kwargs):
        '''
        handle post requests
        '''

        logger = logging.getLogger(__name__) 

        data = json.loads(request.body.decode('utf-8'))

        id = self.get_object().id

        if data["status"] == "getInvitations":
            return getInvitations(data, id)
        elif data["status"] == "getSessions":
            return getSessions(data, id)  
        elif data["status"] == "makeNote":
            return makeNote(request, data, id) 
        elif data["status"] == "deleteNote":
            return deleteNote(request, data, id)       
        elif data["status"] == "getTraits":
            return getTraits(request, data, id)
        elif data["status"] == "editSubject":
            return editSubject(request, data, id)

#store a note about the user
def makeNote(request, data, id):
    logger = logging.getLogger(__name__) 
    logger.info("Make a note")
    logger.info(data)

    u = User.objects.get(id=id)

    n = ProfileNote()
    n.my_profile = u.profile
    n.noteMaker = request.user
    n.text = data["text"].strip().capitalize()

    if n.text != "":
        n.save()

    return getSessions(data,id)

#delete the selected note
def deleteNote(request, data, id):
    logger = logging.getLogger(__name__) 
    logger.info("Delete Note")
    logger.info(data)

    note_id = data["id"]
    n = ProfileNote.objects.get(id=note_id)

    if request.user.is_staff:
        n.delete()

    return getSessions(data, id)

#get full is of subject invitions
def getInvitations(data, id):
    logger = logging.getLogger(__name__) 
    logger.info("Get invitations")
    logger.info(data)

    u=User.objects.get(id=id)

    return JsonResponse({"invitations" :  u.profile.sorted_session_day_list_full(),
                                },safe=False)

#get the session and notes subject has participated in
def getSessions(data, id):
    logger = logging.getLogger(__name__) 
    logger.info("User Info: Get sessions")
    logger.info(data)

    u=User.objects.get(id=id)

    return JsonResponse({"session_day_attended" :  u.profile.sorted_session_day_list_earningsOnly(),
                         "session_day_upcoming" :  u.profile.sorted_session_day_list_upcoming(True),
                         "institutions" : u.profile.get_institution_list(),
                         "subject" : u.profile.json_for_user_info(),
                         "notes" : u.profile.get_notes(),
                            },safe=False,
                        )

#get the traits for this subject
def getTraits(request, data, id):
    logger = logging.getLogger(__name__) 
    logger.info("User Info: Get Traits")
    logger.info(data)

    u=User.objects.get(id=id)

    if not request.user.is_staff:
        return JsonResponse({"subject_traits" :[],},safe=False, )
                            
    return JsonResponse({"subject_traits" : u.profile.sorted_trait_list(),
                            },safe=False,
                        )

#edit the subject
def editSubject(request, data, id):
    logger = logging.getLogger(__name__) 
    logger.info("Edit Subject")
    logger.info(data)

    u=User.objects.get(id=id)

    if not request.user.is_staff:
        return JsonResponse({"status":"fail","errors":{}}, safe=False)

    form_data_dict = data["formData"]

    # for field in data["formData"]:
    #     form_data_dict[field["name"]] = field["value"]

    edit_subject_form = EditSubjectForm(form_data_dict, instance=u.profile)

    if edit_subject_form.is_valid():
        edit_subject_form.save()

        return JsonResponse({"status":"success"}, safe=False)
    
    logger.info("invalid edit subject form")
    return JsonResponse({"status":"fail","errors":dict(edit_subject_form.errors.items())}, safe=False)

