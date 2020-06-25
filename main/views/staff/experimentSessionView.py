from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from main.decorators import user_is_staff
from main.models import experiment_session_days, \
                        experiment_session_day_users, \
                        experiment_sessions, \
                        institutions, \
                        experiments
from main.forms import experimentSessionForm1,experimentSessionForm2,recruitForm
from django.http import JsonResponse
from django.forms.models import model_to_dict
import json
from django.conf import settings
import logging
from django.db.models import CharField,Q,F,Value as V,Subquery
from django.contrib.auth.models import User
import random

#induvidual experiment view
@login_required
@user_is_staff
def experimentSessionView(request,id):
       
    status = ""      

    if request.method == 'POST':
        
        data = json.loads(request.body.decode('utf-8'))         

        try:
            es = experiment_sessions.objects.get(id=id)  
        except es.DoesNotExist:
            raise Http404('Experiment Not Found')               

        if data["status"] == "get":            
            return JsonResponse({"session" :  es.json()}, safe=False)
        elif data["status"] == "updateRecruitmentParameters":
            return updateRecruitmentParameters(data,id)                     
        elif data["status"] ==  "addSessionDay":
           return addSessionDay(data,id)
        elif data["status"] ==  "removeSessionDay":
           return removeSessionDay(data,id)
        elif data["status"] ==  "updateSessionDay":
            return updateSessionDay(data,id)
        elif data["status"] ==  "removeSubject":
            return removeSubject(data)
        elif  data["status"] ==  "findSubjectsToInvite":
            return findSubjectsToInvite(data,id)

    else: #GET             

        return render(request,
                      'staff/experimentSessionView.html',
                      {'form1':experimentSessionForm1(),    
                       'form2':experimentSessionForm2(),    
                       'form3':recruitForm(),                                    
                       'id': id,
                       'session':experiment_sessions.objects.get(id=id)})

#find list of subjects to invite based on recruitment parameters
def findSubjectsToInvite(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Find subjects to invite")
    logger.info(data)

    number = int(data["number"])

    es = experiment_sessions.objects.get(id=id)

    es_genders = es.gender.all()
    es_subjectTypes = es.subject_type.all()
    es_instiutionsInclude = es.institutions_include.all()
    es_institutionsExclude = es.institutions_exclude.all()

    
    logger.info(es_genders)
    logger.info(es_subjectTypes)

    # users=User.objects.annotate(user_institutions_exclude_count = Subquery(es.institutions_exclude.count())) \
    #                   .filter(profile__gender__in = es_genders,
    #                           profile__subjectType__in = es_subjectTypes,
    #                           user_institutions_exclude_count = 0 )

    str='''     -- table of users and institutions they have been in 
                WITH user_institutions AS (SELECT DISTINCT main_institutions.id as institution_id,
                                                        main_institutions.name AS institution_name,
                                                        auth_user.id AS auth_user_id
                                            FROM main_institutions, auth_user
                                            INNER JOIN main_experiment_session_day_users ON main_experiment_session_day_users.attended = 1 AND main_experiment_session_day_users.user_id = auth_user.id
                                            INNER JOIN main_experiment_session_days ON main_experiment_session_day_users.experiment_session_day_id = main_experiment_session_days.id
                                            INNER JOIN main_experiment_sessions ON main_experiment_session_days.experiment_session_id = main_experiment_sessions.id
                                            INNER JOIN main_experiments ON main_experiment_sessions.experiment_id = main_experiments.id
                                            INNER JOIN main_experiments_institutions ON main_experiments.id = main_experiments_institutions.experiment_id AND main_institutions.id = main_experiments_institutions.institution_id
                                            ORDER BY name),
                    
                    --institutions that should subject should not have done already
                    institutions_exclude AS (SELECT main_institutions.id AS institution_id
                                                FROM main_institutions
                                                INNER JOIN main_experiment_sessions_institutions_exclude ON main_institutions.id = main_experiment_sessions_institutions_exclude.institutions_id
                                                WHERE main_experiment_sessions_institutions_exclude.experiment_sessions_id = %s),
                    
                    --institutions that a subject should have done already
                    institutions_include AS (SELECT main_institutions.id AS institution_id
                                                FROM main_institutions
                                                INNER JOIN main_experiment_sessions_institutions_include ON main_institutions.id = main_experiment_sessions_institutions_include.institutions_id
                                                WHERE main_experiment_sessions_institutions_include.experiment_sessions_id = %s),	
                    
                    --table of users that should be excluded based on past history
                    institutions_exclude_user AS (SELECT user_institutions.auth_user_id
                                                    FROM user_institutions
                                                    INNER JOIN institutions_exclude ON institutions_exclude.institution_id = user_institutions.institution_id),
                    
                    --table of users that have at least some of the correct institution experience
                    institutions_include_user AS (SELECT user_institutions.auth_user_id,
                                                        user_institutions.institution_id
                                                    FROM user_institutions
                                                    INNER JOIN institutions_include ON institutions_include.institution_id = user_institutions.institution_id)
                        
                SELECT auth_user.id,
                    auth_user.last_name,
                    auth_user.first_name,
                    
                    (SELECT count(*)                                                     --number of institutions required that subject is in
                        FROM institutions_include) AS institutions_include_count,          
                        
                    (SELECT count(*)                                                     --number of required institutions a subject has been in
                        FROM institutions_include_user
                        INNER JOIN institutions_include ON institutions_include.institution_id = institutions_include_user.institution_id
                        WHERE institutions_include_user.auth_user_id = auth_user.id) as institutions_include_user_count,
                        
                        (SELECT count(*)                                                    --number of institutions subject has participated in that they should not have
                            FROM institutions_exclude_user				  
                            WHERE institutions_exclude_user.auth_user_id = auth_user.id)  as institutions_exclude_user_count
                    
                FROM auth_user

                WHERE institutions_exclude_user_count = 0 AND
                    institutions_include_user_count >= institutions_include_count
                        
                ORDER BY auth_user.last_name, auth_user.first_name'''

    users = User.objects.filter(profile__gender__in = es_genders,
                                profile__subjectType__in = es_subjectTypes) \
                        .raw(str,[id,id])        




    #check user in excluded institions
    # for u in users:
    #     l = institutions.objects.none()
    #     esdus=u.ESDU.all().filter(attended = True)
    #     for i in esdus:
    #         l |= i.experiment_session_day.experiment_session.experiment.institution.all()
        
    #     if l & es_institutionsExclude:
    #         usersTemp.exclude(id = u.id)

    users_json = [u.profile.json_min() for u in users]

    if number > len(users_json):
        usersSmall = users_json
    else:  
        usersSmall = random.sample(users_json,number)

    return JsonResponse({"subjectInvitations" : usersSmall,"status":"success"}, safe=False)

#update the recruitment parameters for this session
def updateRecruitmentParameters(data,id):
    es = experiment_sessions.objects.get(id=id)
    
    form_data_dict = {} 

    genderList=[]
    subjectTypeList=[]
    institutionsExcludeList=[]
    institutionsIncludeList=[]
    experimentsExcludeList=[]
    experimentsIncludeList=[]

    for field in data["formData"]:            
        if field["name"] == "gender":                 
            genderList.append(field["value"])
        elif field["name"] == "subject_type":                 
            subjectTypeList.append(field["value"])
        elif field["name"] == "institutions_exclude":                 
            institutionsExcludeList.append(field["value"])
        elif field["name"] == "institutions_include":                 
            institutionsIncludeList.append(field["value"])
        elif field["name"] == "experiments_exclude":                 
            experimentsExcludeList.append(field["value"])
        elif field["name"] == "experiments_include":                 
            experimentsIncludeList.append(field["value"])
        else:
            form_data_dict[field["name"]] = field["value"]

    form_data_dict["gender"]=genderList
    form_data_dict["subject_type"]=subjectTypeList
    form_data_dict["institutions_exclude"]=institutionsExcludeList
    form_data_dict["institutions_include"]=institutionsIncludeList
    form_data_dict["experiments_exclude"]=experimentsExcludeList
    form_data_dict["experiments_include"]=experimentsIncludeList                       

    #print(form_data_dict)
    form = experimentSessionForm1(form_data_dict,instance=es)

    if form.is_valid():
        #print("valid form")                
        e=form.save()               
        return JsonResponse({"session" : e.json(),"status":"success"}, safe=False)
    else:
        print("invalid form1")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

#add a session day
def addSessionDay(data,id):
    esd=experiment_session_days()
    es = experiment_sessions.objects.get(id=id)

    esd.setup(es)
    esd.save()

    es.save()    

    return JsonResponse({"status":"success","sessionDays":es.json()}, safe=False)

#remove a session day
def removeSessionDay(data,id):
    es = experiment_sessions.objects.get(id=id)

    es.ESD.get(id = data["id"]).delete()
    es.save()

    return JsonResponse({"status":"success","sessionDays":es.json()}, safe=False)

#update session day settings
def updateSessionDay(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Update Session Day")
    logger.info(data)

    es = experiment_sessions.objects.get(id=id)
    esd = experiment_session_days.objects.get(id = data["id"])           

    form_data_dict = {}            

    for field in data["formData"]:           
        form_data_dict[field["name"]] = field["value"]

    form = experimentSessionForm2(form_data_dict,instance=esd)   

    logger.info("here")

    if form.is_valid():
        esd.save()
        es.save()      

        # es = experiment_sessions.objects.get(id=id)

        return JsonResponse({"sessionDays" :es.json(),"status":"success"}, safe=False)
    else:
        print("invalid form2")
        return JsonResponse({"status":"fail","errors":dict(form.errors.items())}, safe=False)

#remove subject from session day 
def removeSubject(data):
    esd=experiment_session_days.objects.get(id= data["id"])
    esdu=esd.experiment_session_day_users.objects.get(id=data["uid"])
    