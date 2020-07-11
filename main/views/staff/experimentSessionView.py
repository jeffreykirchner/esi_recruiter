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
import datetime
from django.db.models import prefetch_related_objects
from .userSearch import lookup
from django.core.serializers.json import DjangoJSONEncoder

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
            return removeSubject(data,id)
        elif  data["status"] ==  "findSubjectsToInvite":
            return findSubjectsToInvite(data,id)
        elif data["status"] == "searchForSubject":
            return getSearchForSubject(data,id)
        elif data["status"] == "manuallyAddSubject":
            return getManuallyAddSubject(data,id)         

    else: #GET             

        return render(request,
                      'staff/experimentSessionView.html',
                      {'form1':experimentSessionForm1(),    
                       'form2':experimentSessionForm2(),    
                       'form3':recruitForm(),                                    
                       'id': id,
                       'session':experiment_sessions.objects.get(id=id)})

#manually search for users to add to session
def getSearchForSubject(data,id):

    logger = logging.getLogger(__name__)
    logger.info("Serch for subject to maually add")
    logger.info(data)

    users_list = lookup(data["searchInfo"],False)

    if len(users_list)>0:
        user_list_valid = getValidUserList(id,users_list)    

    for u in users_list:
        u['valid'] = 0

        #logger.info(str(u['id']))
        #logger.info(str(id))
        #check that subject is not already in
        esdu = experiment_session_day_users.objects.filter(user__id = u['id'],
                                                           experiment_session_day__experiment_session__id = id) \
                                                   .exists()

        if esdu:
            u['alreadyIn'] = 1
        else:
            u['alreadyIn'] = 0

        #check if subject violates recrutment parameters
        for uv in user_list_valid:
            if u['id'] == uv.id:
                u['valid'] = 1

    logger.info(users_list)
    #logger.info(user_list_valid)

    return JsonResponse({"status":"success","users":json.dumps(list(users_list),cls=DjangoJSONEncoder)}, safe=False)

#manually add a single subject
def getManuallyAddSubject(data,id):

    logger = logging.getLogger(__name__)
    logger.info("Manually add subject")
    logger.info(data)

    userID = int(data["userID"])

    #check the subject not already in session
    esdu = experiment_session_day_users.objects.filter(user__id = userID,
                                                           experiment_session_day__experiment_session__id = id) \
                                                   .exists()

    es = experiment_sessions.objects.get(id=id)

    if not esdu:
       es.addUser(userID)
       es.save()

    return JsonResponse({"status":"success","es_min":es.json_esd()}, safe=False)
    
#find list of subjects to invite based on recruitment parameters
def findSubjectsToInvite(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Find subjects to invite")
    logger.info(data)

    number = int(data["number"])

    u_list = getValidUserList(id,[])

    logger.info("Randomly Select:" + str(number)+ " of " + str(len(u_list)))

    if number > len(u_list):
        usersSmall = u_list
    else:  
        usersSmall = random.sample(u_list,number)

    prefetch_related_objects(usersSmall,'profile')

    usersSmall2 = [u.profile.json_min() for u in usersSmall]

    return JsonResponse({"subjectInvitations" : usersSmall2,"status":"success"}, safe=False)

#return a list of all valid users that can participate
def getValidUserList(id,u_list):
    logger = logging.getLogger(__name__)
    logger.info("Get valid user list for session " + str(id))

    es = experiment_sessions.objects.get(id=id)

    institutions_exclude_str = ""
    institutions_include_str = ""
    experiments_exclude_str = ""
    experiments_include_str = ""
    allow_multiple_participations_str = False

    experiment_id = es.experiment.id
    es.experience_min

    #institutions exclude string
    ie_c =  es.institutions_exclude.all().count()
    if ie_c == 0:
        institutions_exclude_str=''
    elif es.institutions_exclude_all:
        institutions_exclude_str = 'institutions_exclude_user_count < ' + str(ie_c) + ' AND '
    else:
        institutions_exclude_str = 'institutions_exclude_user_count = 0 AND '
   
    #institutions include string
    ii_c = es.institutions_include.all().count()
    if ii_c == 0:
        institutions_include_str=''
    elif es.institutions_include_all:
        institutions_include_str = 'institutions_include_user_count = ' + str(ii_c) + ' AND '        
    else:
        institutions_include_str = 'institutions_include_user_count > 0 AND'
    
    #experiments exclude string
    ee_c = es.experiments_exclude.all().count()
    if  ee_c == 0:
        experiments_exclude_str=''
    elif es.experiments_exclude_all:
       experiments_exclude_str = 'experiments_exclude_user_count < ' + str(ee_c) + ' AND '
    else:
        experiments_exclude_str = 'experiments_exclude_user_count = 0 AND '

    #experiments include string
    ei_c = es.experiments_include.all().count()
    if ei_c == 0:
        experiments_include_str=''
    elif es.experiments_include_all:
        experiments_include_str = 'experiments_include_user_count = ' +  str(ei_c) + ' AND '
    else:
        experiments_include_str = 'experiments_include_user_count > 0 AND '

    #allow multiple participations in same experiment
    if es.allow_multiple_participations:
        allow_multiple_participations_str=""
    else:
        allow_multiple_participations_str='''NOT EXISTS(SELECT 1                                                      
			FROM user_experiments
			WHERE user_experiments.user_id = auth_user.id AND user_experiments.experiments_id =''' + str(experiment_id) + ''') AND'''

    institutions_include_user_count_str = ""
    institutions_exclude_user_count_str = ""
    institutions_include_with_str = ""
    institutions_exclude_with_str = ""
    experiments_include_user_count_str = ""
    experiments_exclude_user_count_str = ""
    experiments_include_with_str = ""
    experiments_exclude_with_str = ""
    user_experiments_str = ""
    user_institutions_str= ""

    if ii_c > 0:
        institutions_include_user_count_str = '''
        --number of required institutions a subject has been in
	    (SELECT count(*)                                                    
		   FROM institutions_include_user
		   INNER JOIN institutions_include ON institutions_include.institution_id = institutions_include_user.institution_id
		   WHERE institutions_include_user.auth_user_id = auth_user.id) AS institutions_include_user_count,
        '''

        institutions_include_with_str = '''
        --institutions that a subject should have done already
	    institutions_include AS (SELECT main_institutions.id AS institution_id
								FROM main_institutions
								INNER JOIN main_experiment_sessions_institutions_include ON main_institutions.id = main_experiment_sessions_institutions_include.institutions_id
								WHERE main_experiment_sessions_institutions_include.experiment_sessions_id = ''' + str(id) + '''),

        --table of users that have at least some of the correct institution experience
	    institutions_include_user AS (SELECT user_institutions.auth_user_id,
										   user_institutions.institution_id
				                    FROM user_institutions
				                    INNER JOIN institutions_include ON institutions_include.institution_id = user_institutions.institution_id),
        '''
    
    if ie_c > 0:
       institutions_exclude_user_count_str ='''
       --number of institutions subject has participated in that they should not have		
	   (SELECT count(*)                                                   
	      	FROM institutions_exclude_user				  
		    WHERE institutions_exclude_user.auth_user_id = auth_user.id)  AS institutions_exclude_user_count,
       ''' 
       institutions_exclude_with_str = '''
        --institutions that should subject should not have done already
        institutions_exclude AS (SELECT main_institutions.id AS institution_id
								FROM main_institutions
								INNER JOIN main_experiment_sessions_institutions_exclude ON main_institutions.id = main_experiment_sessions_institutions_exclude.institutions_id
								WHERE main_experiment_sessions_institutions_exclude.experiment_sessions_id = ''' + str(id) + '''), 

        --table of users that should be excluded based on past history
	    institutions_exclude_user AS (SELECT user_institutions.auth_user_id
				                    FROM user_institutions
				                    INNER JOIN institutions_exclude ON institutions_exclude.institution_id = user_institutions.institution_id),
       '''

    if ei_c > 0:
        experiments_include_user_count_str = '''
        --number of required experiments a subject has been in		
	    (SELECT count(*)                                                     
		   FROM user_experiments
		   INNER JOIN experiments_include ON experiments_include.experiments_id = user_experiments.experiments_id
		   WHERE user_experiments.user_id = auth_user.id) AS experiments_include_user_count,
        '''

        experiments_include_with_str = '''
        --experiments that a subject should have done already
	    experiments_include AS (SELECT main_experiments.id AS experiments_id
								FROM main_experiments
								INNER JOIN main_experiment_sessions_experiments_include ON main_experiments.id = main_experiment_sessions_experiments_include.experiments_id
								WHERE main_experiment_sessions_experiments_include.experiment_sessions_id = ''' + str(id) + '''),
        '''
    if ee_c > 0:
        experiments_exclude_user_count_str = '''
        --number of excluded experiments a subject has been in		
	    (SELECT count(*)                                                    
		   FROM user_experiments
		   INNER JOIN experiments_exclude ON experiments_exclude.experiments_id = user_experiments.experiments_id
		   WHERE user_experiments.user_id = auth_user.id) AS experiments_exclude_user_count, 
        '''

        experiments_exclude_with_str = '''
        --experiments that should subject should not have done already
        experiments_exclude AS (SELECT main_experiments.id AS experiments_id
								FROM main_experiments
								INNER JOIN main_experiment_sessions_experiments_exclude ON main_experiments.id = main_experiment_sessions_experiments_exclude.experiments_id
								WHERE main_experiment_sessions_experiments_exclude.experiment_sessions_id = ''' + str(id) + '''),
        '''

    exeriments_count_select_str =""
    exeriments_count_select_where=""


    if es.experience_constraint:
        exeriments_count_select_str ='''
            --the number of experiments a subject has attended	
        (SELECT count(*)                                                     
                FROM main_experiment_session_day_users
                WHERE main_experiment_session_day_users.user_id = auth_user.id AND attended = 1) AS experiments_attended_count,
        '''
        exeriments_count_select_where ='''
        experiments_attended_count >= ''' + str(es.experience_min) + ''' AND       --minimum number of experiments subject has been in
        experiments_attended_count <=  ''' + str(es.experience_max) + ''' AND      --max number of experiments a subject has be in
        '''

    #if ee_c > 0 or ei_c > 0:

    user_experiments_str = '''
        --table of users and experiments they have been in	
	    user_experiments AS (SELECT DISTINCT main_experiments.id as experiments_id,
										 main_experiment_sessions.id as experiment_sessions_id,
										 main_experiment_session_day_users.user_id as user_id
						 FROM main_experiments
						 INNER JOIN main_experiment_sessions ON main_experiment_sessions.experiment_id = main_experiments.id
						 INNER JOIN main_experiment_session_days ON main_experiment_session_days.experiment_session_id = main_experiment_sessions.id
						 INNER JOIN main_experiment_session_day_users ON main_experiment_session_day_users.experiment_session_day_id = main_experiment_session_days.id
						 WHERE main_experiment_session_day_users.attended = 1 OR
						      (main_experiment_session_day_users.confirmed = 1 AND main_experiment_session_days.date >  CURRENT_TIMESTAMP)),
        '''                              

    if ii_c > 0 or ie_c > 0:
        user_institutions_str ='''
        -- table of users and institutions they have been in 
        user_institutions AS (SELECT DISTINCT main_institutions.id as institution_id,
										   --main_institutions.name AS institution_name,
										   main_experiment_session_day_users.user_id AS auth_user_id
							FROM main_institutions
							INNER JOIN main_experiment_session_day_users ON main_experiment_session_day_users.experiment_session_day_id = main_experiment_session_days.id
							INNER JOIN main_experiment_session_days ON main_experiment_session_days.experiment_session_id = main_experiment_sessions.id
							INNER JOIN main_experiment_sessions ON main_experiment_sessions.experiment_id = main_experiments.id
							INNER JOIN main_experiments ON main_experiments.id = main_experiments_institutions.experiment_id
							INNER JOIN main_experiments_institutions ON main_experiments.id = main_experiments_institutions.experiment_id AND
						                                            	main_institutions.id = main_experiments_institutions.institution_id
							WHERE main_experiment_session_day_users.attended = 1 AND
							      main_institutions.id = main_experiments_institutions.institution_id),
    '''

    #list of users to search for, if empty return all valid users
    users_to_search_for=""
    if len(u_list) > 0:
        #logger.info(u_list)
        users_to_search_for = "("
        for u in u_list:
            if( users_to_search_for != "("):
                users_to_search_for += " OR "

            users_to_search_for += 'auth_user.id = ' + str(u['id'])

        users_to_search_for += ") AND"

    str1='''          	  									
        WITH
        --table of genders required in session
        genders_include AS (SELECT genders_id
					     FROM main_experiment_sessions_gender
			             WHERE main_experiment_sessions_gender.experiment_sessions_id = ''' + str(id) + '''),
	
        ''' \
        + user_institutions_str \
        + institutions_include_with_str \
        + institutions_exclude_with_str \
        + experiments_exclude_with_str \
        + experiments_include_with_str \
        + user_experiments_str \
        +'''
        
        --table of subject types required in session
        subject_type_include AS (SELECT subject_types_id
                                FROM main_experiment_sessions_subject_type
                                WHERE main_experiment_sessions_subject_type.experiment_sessions_id = ''' + str(id) + ''')

        SELECT        
       '''\
       + institutions_exclude_user_count_str \
       + institutions_include_user_count_str \
       + experiments_exclude_user_count_str \
       + experiments_include_user_count_str \
       + exeriments_count_select_str \
       + '''             		
	   
       auth_user.id,
	   auth_user.last_name,
	   auth_user.first_name
			 	
       FROM auth_user

       INNER JOIN main_profile ON main_profile.user_id = auth_user.id

       WHERE '''\
       + institutions_exclude_str \
       + institutions_include_str \
       + '''
       --user's gender is on the list
	   EXISTS(SELECT 1                                                    
			FROM genders_include	
			WHERE main_profile.gender_id = genders_include.genders_id) AND   

       --user's subject type is on the list
	   EXISTS(SELECT 1                                                   
			FROM subject_type_include	
			WHERE main_profile.subjectType_id = subject_type_include.subject_types_id) > 0 AND        

       --user is not already invited to session     
       NOT EXISTS(SELECT 1
            FROM user_experiments
            WHERE user_experiments.experiment_sessions_id = ''' + str(id) + ''' AND user_experiments.user_id = auth_user.id) AND 

       '''\
       + experiments_exclude_str \
       + experiments_include_str \
       + exeriments_count_select_where \
       + allow_multiple_participations_str \
       + users_to_search_for \
 	   + '''      
	   is_staff = 0 AND                                                 --subject cannot be an ESI staff memeber
	   is_active = 1                                                    --acount is activated

       '''

    #str1 = str1.replace("10256","%s")

    # logger.info(str)

    users = User.objects.raw(str1) #institutions_exclude_str,institutions_include_str,experiments_exclude_str,experiments_include_str

    #log sql statement
    logger.info(users)

    time_start = datetime.datetime.now()
    u_list = list(users)
    time_end = datetime.datetime.now()
    time_span = time_end-time_start

    logger.info("SQL Run time: " + str(time_span.total_seconds()))

    return u_list

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
    logger = logging.getLogger(__name__)
    logger.info("Add session day")
    logger.info(data)

    esd = experiment_session_days()
    es = experiment_sessions.objects.get(id=id)

    u_list = es.ESD.first().getListOfUserIDs()

    #for i in id_list:
    #    logger.info(i)

    # logger.info(u_list)

    esd.setup(es,u_list)
    esd.save()

    es.save()    

    return JsonResponse({"status":"success","sessionDays":es.json()}, safe=False)

#remove a session day
def removeSessionDay(data,id):
    es = experiment_sessions.objects.get(id=id)

    esd = es.ESD.get(id = data["id"])

    if esd.allowDelete():
        esd.delete()

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
def removeSubject(data,id):
    logger = logging.getLogger(__name__)
    logger.info("Remove subject from session")
    logger.info(data)

    userId = data['userId']
    esduId = data['esduId']    

    esdu=experiment_session_day_users.objects.filter(user__id = userId,
                                                     experiment_session_day__experiment_session__id = id)

    logger.info(esdu)
    #delete sessions users only if they have not earned money
    for i in esdu:
        if i.allowDelete():
            i.delete()            

    es = experiment_sessions.objects.get(id=id)
    return JsonResponse({"status":"success","es_min":es.json_esd()}, safe=False)
    

    