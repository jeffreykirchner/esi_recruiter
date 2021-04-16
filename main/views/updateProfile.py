'''
update profile view
'''
import logging
import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.db.models import CharField, F, Value as V
from django.http import JsonResponse

from main.models import help_docs
from main.forms import profileFormUpdate
from main.globals import profile_create_send_email

#user account info
@login_required
def updateProfile(request):
    '''
    update profile view
    '''

    logger = logging.getLogger(__name__)

    if request.method == 'POST':

        data = json.loads(request.body.decode('utf-8'))

        #check for correct action
        action = data.get("action", "fail")

        if action == "update":
            return update_profile(request, data)

        #valid action not found
        logger.warning(f"Profile update post error: {request.user}")
        return JsonResponse({"status" :  "error"}, safe=False)

    else:
        logger.info("show profile")

        form = profileFormUpdate(
            initial={'first_name': request.user.first_name,
                     'last_name': request.user.last_name,
                     'chapman_id': request.user.profile.studentID,
                     'email':request.user.email,
                     'gender':request.user.profile.gender.id,
                     'phone':request.user.profile.phone,
                     'major':request.user.profile.major.id,
                     'subject_type':request.user.profile.subject_type.id,
                     'studentWorker':"Yes" if request.user.profile.studentWorker else "No",
                     'paused':"Yes" if request.user.profile.paused else "No"}
        )

        try:
            helpText = help_docs.objects.annotate(rp = V(request.path, output_field=CharField()))\
                                        .filter(rp__icontains=F('path')).first().text

        except Exception  as e:
            helpText = "No help doc was found."

        form_ids = []
        for i in form:
            form_ids.append(i.html_name)

        return render(request, 'profile.html', {'form': form,
                                                'form_ids': form_ids,
                                                'helpText': helpText})


def update_profile(request, data):
    '''
    update user's profile
    '''
    logger = logging.getLogger(__name__)
    logger.info(f"Update Profile: {request.user}")

    form_data_dict = {}

    for field in data["formData"]:
        form_data_dict[field["name"]] = field["value"]

    form = profileFormUpdate(form_data_dict, user=request.user)

    if form.is_valid():

        u = request.user
        email_verification_required = False

        if u.email != form.cleaned_data['email'].lower():
            email_verification_required = True

        u.first_name = form.cleaned_data['first_name'].strip().capitalize()
        u.last_name = form.cleaned_data['last_name'].strip().capitalize()
        u.email = form.cleaned_data['email'].strip().lower()
        u.username = u.email

        u.profile.studentID = form.cleaned_data['chapman_id'].strip()
        u.profile.gender = form.cleaned_data['gender']
        u.profile.subjecType = form.cleaned_data['subject_type']
        u.profile.studentWorker = form.cleaned_data['studentWorker']
        u.profile.phone = form.cleaned_data['phone'].strip()
        u.profile.major = form.cleaned_data['major']
        u.profile.paused = form.cleaned_data['paused']

        if form.cleaned_data['password1']:
            if form.cleaned_data['password1'] != "":
                u.set_password(form.cleaned_data['password1'])

        if email_verification_required:
            u.profile.email_confirmed = "no"
            profile_create_send_email(request, u)

        u.save()
        u.profile.save()
        u.profile.setup_email_filter()

        return JsonResponse({"status" : "success", "email_verification_required":email_verification_required}, safe=False)

    else:
        logger.info(f"Update profile validation error {request.user}")
        return JsonResponse({"status":"error", "errors":dict(form.errors.items())}, safe=False)

