from random import randrange
from datetime import datetime
from tinymce.models import HTMLField
from functools import reduce
from operator import or_

import logging
import pytz

from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.urls import reverse
from django.db.models import Q, F, Value as V, Count

from main.models import experiments
from main.models import parameters
from main.models import recruitment_parameters
from main.models import parameters
from main.models import ConsentForm

import main

#session for an experiment (could last multiple days)
class experiment_sessions(models.Model):
    experiment = models.ForeignKey(experiments, on_delete=models.CASCADE, related_name='ES')  
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creator',blank=True, null=True,)   #user that created the session
    consent_form = models.ForeignKey(ConsentForm, on_delete=models.CASCADE, null=True)                           #consent form used for new sessions
    recruitment_params = models.ForeignKey(recruitment_parameters, on_delete=models.CASCADE, null=True)

    canceled = models.BooleanField(default=False)
    invitation_text = HTMLField(default="")                                 #text of email invitation subjects receive

    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "ID: " + str(self.id)

    class Meta:
        verbose_name = 'Experiment Sessions'
        verbose_name_plural = 'Experiment Sessions'

    #get list of confirmed user emails
    def getConfirmedEmailList(self):

        l = main.models.experiment_session_day_users.objects.filter(experiment_session_day__experiment_session__id = self.id)\
                                                .filter(confirmed = True)\
                                                .select_related('user')\
                                                .values('user__email','user__id','user__first_name','user__last_name')\
                                                .order_by('user__email')\
                                                .distinct()   


        return [{"user_email": i['user__email'],
                 "user_id":i['user__id'],
                 "user_first_name":i['user__first_name'],
                 "user_last_name":i['user__last_name'],} for i in l ]

    #check if specifed user is in this sessoin
    def checkUserInSession(self,check_user):

        for e in self.ESD.all():
            if e.checkUserInSession(check_user):
                return True

        return False

    #build an invition email given the experiment session
    def getInvitationEmail(self):
        logger = logging.getLogger(__name__)

        p = parameters.objects.first()
       
        message = ""

        message = str(self.invitation_text)

        message = message.replace("[confirmation link]", p.siteURL)
        message = message.replace("[session length]",self.getSessionDayLengthString())
        message = message.replace("[session date and time]",self.getSessionDayDateString())
        message = message.replace("[on time bonus]","$" + self.experiment.getShowUpFeeString())
        message = message.replace("[contact email]", p.labManager.email)
        message = message.replace("[profile link]",p.siteURL + reverse('profile'))
        message = message.replace("[session id]", str(self.id))

        return message
    
    #build a cancelation email for this experiment session
    def getCancelationEmail(self):
        p = parameters.objects.first()

        message = ""

        message = p.cancelationText
        message = message.replace("[session date and time]", self.getSessionDayDateString())
        message = message.replace("[contact email]", p.labManager.email)

        return message

    #add new user to session
    def addUser(self, userID, staffUser, manuallyAdded):
        for esd in self.ESD.all():
            esd.addUser(userID,staffUser,manuallyAdded)  

    #get a string of sessions day dates
    def getSessionDayDateString(self):
        tempS = ""

        ESD_list = list(self.ESD.all().order_by("date"))
        ESD_list_length=len(ESD_list)

        for i in ESD_list:
            if tempS != "":
                if ESD_list.index(i) == ESD_list_length-1:
                     tempS += " and "
                else:
                    tempS += ", "
        
            tempS += i.getDateString()
        
        return tempS

    #get a string of sessions day lengths
    def getSessionDayLengthString(self):
        tempS = ""

        ESD_list = list(self.ESD.all().order_by("date"))
        ESD_list_length=len(ESD_list)

        for i in ESD_list:
            if tempS != "":
                if ESD_list.index(i) == ESD_list_length-1:
                     tempS += " and "
                else:
                    tempS += ", "
        
            tempS += i.getLengthString()

        return tempS      

    #setup this session with defualt parameters from related experiment
    def setupRecruitment(self):

        p = self.experiment.recruitment_params_default

        tempP = recruitment_parameters()
        tempP.setup(p)
        tempP.save()

        self.recruitment_params = tempP
        self.recruitment_params.save()
        self.save()

        return self

    #check if this session can be deleted    
    def allowDelete(self):

        #if subjects have been invited, session cannot be deleted
        if main.models.experiment_session_day_users.objects.filter(experiment_session_day__experiment_session__id = self.id).count() > 0:
            return False
        else:
            return True
        
        # if self.canceled and 
           

        # ESD = self.ESD.all()    

        # for e in ESD:
        #     if not e.allowDelete():
        #         return False

       # return True

    #check if any of the session days are complete
    def allowEdit(self):
        ESD_complete = self.ESD.filter(complete = True)

        if len(ESD_complete) > 0:
            return False

        return True

    #return a list of all valid users that can participate
    #u_list confine search to list, empty for all subjects
    #checkAlreadyIn checks if a subject is already added to session
    #if testExperiment is greater than 0, use to test valid list if user were to hypothetically participate in that experiment
    #if testsession is greater than 0, use to ""
    def getValidUserList(self, u_list, checkAlreadyIn, testExperiment, testSession, testInstiutionList, printSQL):
        logger = logging.getLogger(__name__)
        logger.info("Get valid user list for session " + str(self))

        # if u_list==[]:
        #     u_list = User.objects.filter(is_active=True).values("id")

        es = self
        es_p = es.recruitment_params
        id =  self.id
        p = parameters.objects.first()

        experiment_id = es.experiment.id

        #institutions exclude count
        ie_c =  es_p.institutions_exclude.all().count()
        if not es_p.institutions_exclude_all and ie_c > 1:
            ie_c = 1
    
        #institutions include count
        ii_c = es_p.institutions_include.all().count()
        if not es_p.institutions_include_all and ii_c > 1:
            ii_c = 1     

        #experiments exclude count
        ee_c = es_p.experiments_exclude.all().count()
        if not es_p.experiments_exclude_all and ee_c > 1:
            ee_c = 1

        #experiments include count
        ei_c = es_p.experiments_include.all().count()
        if not es_p.experiments_include_all and ei_c > 1:
            ei_c = 1        

        #allow multiple participations in same experiment
        allow_multiple_participations_str=""
        if not es_p.allow_multiple_participations:
            allow_multiple_participations_str=f'''
            --check that user has not already done this experiment
            NOT EXISTS(SELECT 1                                                   
                       FROM user_experiments
                       WHERE user_experiments.user_id = auth_user.id AND
                             experiment_sessions_id != {id} AND
                             user_experiments.experiments_id = {experiment_id}) AND
            '''   

        #institutions include strings
        institutions_include_user_where_str = ""
        institutions_include_with_str = ""
        if ii_c > 0:
            institutions_include_user_where_str = '''
            --check that subject has been in correct number of insitutions
            EXISTS (SELECT 1                                                    
                FROM institutions_include_user                
                WHERE institutions_include_user.id = auth_user.id) AND 
            '''

            institutions_include_with_str = f'''
            --institutions that a subject should have done already
            institutions_include AS (SELECT institutions_id
                                        FROM main_recruitment_parameters_institutions_include
                                        INNER JOIN main_recruitment_parameters ON main_recruitment_parameters.id = main_recruitment_parameters_institutions_include.recruitment_parameters_id
                                        INNER JOIN main_experiment_sessions ON main_experiment_sessions.recruitment_params_id = main_recruitment_parameters.id
                                        WHERE main_experiment_sessions.id = {id}),

            --table of users that have the correct institution experience
            institutions_include_user AS (SELECT user_institutions_past.auth_user_id as id
                                            FROM user_institutions_past
                                            INNER JOIN institutions_include ON institutions_include.institutions_id = user_institutions_past.institution_id
                                            GROUP BY user_institutions_past.auth_user_id
                                            HAVING count(user_institutions_past.auth_user_id) >= {ii_c}),
            '''
        
        #institution exclude strings
        institutions_exclude_user_where_str = ""
        institutions_exclude_with_str = ""
        if ie_c > 0:
            institutions_exclude_user_where_str ='''
                --check if subject has not partipated in institutions they should not have		
                NOT EXISTS (SELECT 1                                                    
                        FROM institutions_exclude_user                
                        WHERE institutions_exclude_user.id = auth_user.id) AND
                ''' 
            institutions_exclude_with_str = f'''
                --institutions that should subject should not have done already
                institutions_exclude AS (SELECT institutions_id
                                            FROM main_recruitment_parameters_institutions_exclude
                                            INNER JOIN main_recruitment_parameters ON main_recruitment_parameters.id = main_recruitment_parameters_institutions_exclude.recruitment_parameters_id
                                            INNER JOIN main_experiment_sessions ON main_experiment_sessions.recruitment_params_id = main_recruitment_parameters.id
                                            WHERE main_experiment_sessions.id = {id}), 

                --table of users that should be excluded based on past history
                institutions_exclude_user AS (SELECT user_institutions.auth_user_id as id
                                                FROM user_institutions
                                                INNER JOIN institutions_exclude ON institutions_exclude.institutions_id = user_institutions.institution_id
                                                GROUP BY user_institutions.auth_user_id
                                                HAVING count(user_institutions.auth_user_id) >= {ie_c}),
                '''

        #experiments include strings
        experiments_include_user_where_str = ""
        experiments_include_with_str = ""
        if ei_c > 0:
            experiments_include_user_where_str = '''
            --check that user has been in required experiments	
            EXISTS (SELECT 1                                                    
                FROM experiments_include_user                
                WHERE experiments_include_user.id = auth_user.id) AND
            '''

            experiments_include_with_str = f'''
            --table of experiments that a subject should have done already
            experiments_include AS (SELECT experiments_id
                                        FROM main_recruitment_parameters_experiments_include
                                        INNER JOIN main_recruitment_parameters ON main_recruitment_parameters.id = main_recruitment_parameters_experiments_include.recruitment_parameters_id
                                        INNER JOIN main_experiment_sessions ON main_experiment_sessions.recruitment_params_id = main_recruitment_parameters.id
                                        WHERE main_experiment_sessions.id = {id}),
            

            --table of users that have the correct experiment include experience
            experiments_include_user AS(SELECT user_experiments_past.user_id as id
                                        FROM user_experiments_past
                                        INNER JOIN experiments_include ON experiments_include.experiments_id = user_experiments_past.experiments_id
                                        GROUP BY user_experiments_past.user_id
                                        HAVING count(user_experiments_past.user_id) >= {ei_c}),
            '''

        #experiments exclude strings
        experiments_exclude_user_where_str = ""
        experiments_exclude_with_str=""
        if ee_c > 0:
            experiments_exclude_user_where_str = '''
            --check that user has not been in excluded experiments		
            NOT EXISTS (SELECT 1                                                    
                FROM experiments_exclude_user                
                WHERE experiments_exclude_user.id = auth_user.id) AND 
            '''

            experiments_exclude_with_str = f'''
            --experiments that subject should not have done already
            experiments_exclude AS (SELECT experiments_id
                                    FROM main_recruitment_parameters_experiments_exclude
                                    INNER JOIN main_recruitment_parameters ON main_recruitment_parameters.id = main_recruitment_parameters_experiments_exclude.recruitment_parameters_id
                                    INNER JOIN main_experiment_sessions ON main_experiment_sessions.recruitment_params_id = main_recruitment_parameters.id
                                    WHERE main_experiment_sessions.id = {id}),

            --table of users that have the correct experiment exclude experience
            experiments_exclude_user AS(SELECT user_experiments.user_id as id
                                        FROM user_experiments
                                        INNER JOIN experiments_exclude ON experiments_exclude.experiments_id = user_experiments.experiments_id
                                        GROUP BY user_experiments.user_id
                                        HAVING count(user_experiments.user_id) >= {ee_c}),
            '''

        #list of users to search for, if empty return all valid users
        users_to_search_for=""
        user_to_search_for_list_str = ""
        user_to_search_for_list_values_str=""
        if len(u_list) > 0:
            logger.info(u_list)
            user_to_search_for_list_str = "("
            for u in u_list:
                if( user_to_search_for_list_str != "("):
                    user_to_search_for_list_str += " , "
                    user_to_search_for_list_values_str +=", "

                user_to_search_for_list_str += str(u['id'])
                user_to_search_for_list_values_str +="(" + str(u['id']) + ")"

            user_to_search_for_list_str += ")"

            users_to_search_for += 'auth_user.id IN ' + user_to_search_for_list_str + ' AND '
        
        #user experiments past only
        user_experiments_past_str = ""
        if ei_c > 0:
            user_experiments_past_str= f'''
                --table of users and experiments they have been in or commited to be in
                user_experiments_past AS (SELECT main_experiments.id as experiments_id,
                                                main_experiment_sessions.id as experiment_sessions_id,
                                                main_experiment_session_day_users.user_id as user_id
                                FROM main_experiments
                                INNER JOIN main_experiment_sessions ON main_experiment_sessions.experiment_id = main_experiments.id
                                INNER JOIN main_experiment_session_days ON main_experiment_session_days.experiment_session_id = main_experiment_sessions.id
                                INNER JOIN main_experiment_session_day_users ON main_experiment_session_day_users.experiment_session_day_id = main_experiment_session_days.id
                                WHERE main_experiment_sessions.canceled = FALSE AND
                                      main_experiment_session_day_users.attended = TRUE
                                '''

            if len(u_list) > 0:
                user_experiments_past_str +=f''' AND
                                    main_experiment_session_day_users.user_id IN {user_to_search_for_list_str}  
                    '''

            user_experiments_past_str +='''),'''

        #user experiments list past and future
        user_experiments_str = f'''
            --table of users and experiments they have been in or commited to be in
            user_experiments AS (SELECT main_experiments.id as experiments_id,
                                            main_experiment_sessions.id as experiment_sessions_id,
                                            main_experiment_session_day_users.user_id as user_id
                            FROM main_experiments
                            INNER JOIN main_experiment_sessions ON main_experiment_sessions.experiment_id = main_experiments.id
                            INNER JOIN main_experiment_session_days ON main_experiment_session_days.experiment_session_id = main_experiment_sessions.id
                            INNER JOIN main_experiment_session_day_users ON main_experiment_session_day_users.experiment_session_day_id = main_experiment_session_days.id
                            WHERE main_experiment_sessions.canceled = FALSE AND
                                  (main_experiment_session_day_users.attended = TRUE OR
                                    (main_experiment_session_day_users.confirmed = TRUE AND 
                                     main_experiment_session_days.date_end BETWEEN CURRENT_TIMESTAMP AND '{self.getLastDate()}'))
                            '''

        if len(u_list) > 0:
            user_experiments_str +=f''' AND
                                  main_experiment_session_day_users.user_id IN {user_to_search_for_list_str}  
                '''

        if testExperiment > 0:
            user_experiments_str +=f'''
                                    --add test experiment and session in to check if violation occurs
                                    UNION   
                                    SELECT {testExperiment} as experiments_id,
                                           {testSession} as experiment_sessions_id, 
                                           v.user_id as user_id
		                            FROM (VALUES {user_to_search_for_list_values_str}) AS v(user_id)
                                    '''
        user_experiments_str +='''),'''

        #list of users in current session
        user_current_sesion_str = f'''
            ---table of users that have been invited to the current session
            user_current_sesion AS (SELECT main_experiment_sessions.id as experiment_sessions_id,
                                        main_experiment_session_day_users.user_id as user_id
                                FROM main_experiment_sessions
                                INNER JOIN main_experiment_session_days ON main_experiment_session_days.experiment_session_id = main_experiment_sessions.id
                                INNER JOIN main_experiment_session_day_users ON main_experiment_session_day_users.experiment_session_day_id = main_experiment_session_days.id
                                WHERE main_experiment_sessions.id = {id}),
        '''                                    

        #list of institutions subject has been in in the past
        user_institutions_past_str=""
        if ii_c > 0:
            user_institutions_past_str =f'''
            -- table of users and institutions they have been in past
            user_institutions_past AS (SELECT DISTINCT main_institutions.id as institution_id,
                                                       --main_institutions.name AS institution_name,
                                                       main_experiment_session_day_users.user_id AS auth_user_id
                                FROM main_institutions
                                INNER JOIN main_experiments_institutions ON main_experiments_institutions.institution_id = main_institutions.id
                                INNER JOIN main_experiments ON main_experiments.id = main_experiments_institutions.experiment_id
                                INNER JOIN main_experiment_sessions ON main_experiment_sessions.experiment_id = main_experiments.id
                                INNER JOIN main_experiment_session_days ON main_experiment_session_days.experiment_session_id = main_experiment_sessions.id
                                INNER JOIN main_experiment_session_day_users ON main_experiment_session_day_users.experiment_session_day_id = main_experiment_session_days.id
                                WHERE main_experiment_sessions.canceled = FALSE AND
                                      main_experiment_session_day_users.attended = TRUE AND            
                                      main_institutions.id = main_experiments_institutions.institution_id
            '''

            if len(u_list) > 0:
                user_institutions_past_str +=f''' AND       
                                       main_experiment_session_day_users.user_id IN {user_to_search_for_list_str} 
                    '''
            user_institutions_past_str +='''),'''

        #list of institutions subject has been in or are commited to be in in the future
        user_institutions_str=""
        if ie_c > 0:
            user_institutions_str =f'''
            -- table of users and institutions they have been in 
            user_institutions AS (SELECT DISTINCT main_institutions.id as institution_id,
                                            --main_institutions.name AS institution_name,
                                            main_experiment_session_day_users.user_id AS auth_user_id
                                FROM main_institutions
                                INNER JOIN main_experiments_institutions ON main_experiments_institutions.institution_id = main_institutions.id
                                INNER JOIN main_experiments ON main_experiments.id = main_experiments_institutions.experiment_id
                                INNER JOIN main_experiment_sessions ON main_experiment_sessions.experiment_id = main_experiments.id
                                INNER JOIN main_experiment_session_days ON main_experiment_session_days.experiment_session_id = main_experiment_sessions.id
                                INNER JOIN main_experiment_session_day_users ON main_experiment_session_day_users.experiment_session_day_id = main_experiment_session_days.id
                                WHERE main_experiment_sessions.canceled = FALSE AND
                                       (main_experiment_session_day_users.attended = TRUE OR
                                         (main_experiment_session_day_users.confirmed = TRUE AND 
                                        main_experiment_session_days.date_end BETWEEN CURRENT_TIMESTAMP AND '{self.getLastDate()}') AND            
                                        main_institutions.id = main_experiments_institutions.institution_id)
            '''

            if len(u_list) > 0:
                user_institutions_str +=f''' AND       
                                       main_experiment_session_day_users.user_id IN {user_to_search_for_list_str} 
                    '''
            
            if testExperiment > 0:
                for i in testInstiutionList:
                    user_institutions_str +=f'''
                                    --add test institutions in to check if violation occurs
                                    UNION   
                                    SELECT {i} as institution_id,
                                           v.user_id as auth_user_id
		                            FROM (VALUES {user_to_search_for_list_values_str}) AS v(user_id)
                                    '''
            user_institutions_str +='''),'''

        #check that subject is not already invited to session
        user_not_in_session_already=""
        if checkAlreadyIn:
            user_not_in_session_already = '''
            --user is not already invited to session     
            NOT EXISTS(SELECT 1
                    FROM user_current_sesion
                    WHERE user_current_sesion.user_id = auth_user.id) AND 
            '''
        
        #check genders
        gender_with_str=""
        gender_where_str=""
        if checkAlreadyIn:
            #only check genders during invitation phase
            gender_with_str=f'''
                --table of genders required in session
                genders_include AS (SELECT genders_id
                                FROM main_recruitment_parameters_gender
                                INNER JOIN main_recruitment_parameters ON main_recruitment_parameters.id = main_recruitment_parameters_gender.recruitment_parameters_id
                                INNER JOIN main_experiment_sessions ON main_experiment_sessions.recruitment_params_id = main_recruitment_parameters.id
                                WHERE main_experiment_sessions.id = {id}),
            '''

            gender_where_str=f'''
                --user's gender is on the list
                EXISTS(SELECT 1                                                   
                    FROM genders_include	
                    WHERE main_profile.gender_id = genders_include.genders_id) AND 
            '''

        str1=f'''          	  									
            WITH
            {gender_with_str}
            
            {user_institutions_str}
            {user_institutions_past_str}
            {institutions_include_with_str}
            {institutions_exclude_with_str}

            {user_experiments_past_str}
            {user_experiments_str}
            {experiments_exclude_with_str}
            {experiments_include_with_str}
            {user_current_sesion_str}

            --table of subject types required in session
            subject_type_include AS (SELECT subject_types_id
                                        FROM main_recruitment_parameters_subject_type
                                        INNER JOIN main_recruitment_parameters ON main_recruitment_parameters.id = main_recruitment_parameters_subject_type.recruitment_parameters_id
                                        INNER JOIN main_experiment_sessions ON main_experiment_sessions.recruitment_params_id = main_recruitment_parameters.id
                                        WHERE main_experiment_sessions.id = {id})

            SELECT                 		
            
            auth_user.id,
            auth_user.last_name,
            auth_user.first_name

            FROM auth_user

            INNER JOIN main_profile ON main_profile.user_id = auth_user.id

            WHERE 
            auth_user.is_active = TRUE  AND                                  --acount is activated
            auth_user.is_staff = FALSE AND                                   --subject cannot be an admin memeber
            main_profile.blackballed = FALSE AND                             --subject has not been blackballed  
            main_profile.type_id = 2 AND                                     --only subjects 
            main_profile.email_confirmed = 'yes' AND                          --the email address has been confirmed

            {users_to_search_for}

            {institutions_exclude_user_where_str}
            {institutions_include_user_where_str}
            {experiments_exclude_user_where_str}
            {experiments_include_user_where_str}
            
            {gender_where_str}             

            --user's subject type is on the list
            EXISTS(SELECT 1                                                   
                    FROM subject_type_include	
                    WHERE main_profile.subject_type_id = subject_type_include.subject_types_id) AND 

            {user_not_in_session_already}
            {allow_multiple_participations_str}

            main_profile.paused = FALSE                                      --check that the subject has not paused their account
            '''

        #str1 = str1.replace("10256","%s")

        #logger.info(str1)

        users = User.objects.raw(str1) #institutions_exclude_str,institutions_include_str,experiments_exclude_str,experiments_include_str

        #log sql statement
        if printSQL:
            logger.info(users)

        time_start = datetime.now()
        u_list = list(users)
        time_end = datetime.now()
        time_span = time_end-time_start

        logger.info("SQL Run time: " + str(time_span.total_seconds()))

        return u_list

    #gets the valid list from getValidUserList then clean it based on future confermations
    #max_user_count max number of users to return, randomize otherwise
    def getValidUserList_forward_check(self,u_list,checkAlreadyIn,testExperiment,testSession,testInstiutionList,printSQL,max_user_count):
        logger = logging.getLogger(__name__)

        user_list_valid_clean=[]

        #valid list based on current experience
        user_list_valid = self.getValidUserList(u_list, checkAlreadyIn, testExperiment, testSession, testInstiutionList, printSQL) 

        #logger.info(f'getValidUserList_forward_check found {user_list_valid}')

        #check django based constraints
        user_list_valid = self.getValidUserListDjango(user_list_valid,checkAlreadyIn,testExperiment,testSession,testInstiutionList,printSQL)

        logger.info(f'getValidUserList_forward_check found {user_list_valid}')

        if max_user_count == 0:
            max_user_count = len(user_list_valid)

        first_date = self.getFirstDate()
        i_list = self.experiment.institution.values_list("id", flat=True)
        experiment_id = self.experiment.id

        while len(user_list_valid_clean) < max_user_count and len(user_list_valid)>0:
            n = randrange(0, len(user_list_valid))

            u = user_list_valid.pop(n)

            if not u.profile.check_for_future_constraints(self, first_date, i_list, experiment_id):
                user_list_valid_clean.append(u)
        
        return user_list_valid_clean

    #do django validation of user list
    def getValidUserListDjango(self, u_list, checkAlreadyIn, testExperiment, testSession, testInstiutionList, printSQL):

        logger = logging.getLogger(__name__)
        
        #logger.info(f"{u_list}")
        #check experience count
        u_list = self.getValidUserList_school_exclude(u_list, testExperiment)
        #logger.info(f"{u_list}")
        u_list = self.getValidUserList_school_include(u_list, testExperiment)
        #logger.info(f"{u_list}")
        u_list = self.getValidUserList_check_experience(u_list, testExperiment)
        #logger.info(f"{u_list}")
        u_list = self.getValidUserList_trait_constraints(u_list, testExperiment)
        #logger.info(f"{u_list}")
        u_list = self.getValidUserList_trait_constraints_exclude(u_list, testExperiment)
        #logger.info(f"{u_list}")
        u_list = self.getValidUserList_date_time_overlap(u_list, testSession)
        #logger.info(f"{u_list}")
        u_list = self.getValidUserList_check_now_show_block(u_list)

        return u_list
    
    #return a valid subset of users who not in excluded schools
    def getValidUserList_school_exclude(self, u_list, testExperiment):
        logger = logging.getLogger(__name__)
        logger.info(f"getValidUserList_school_exclude {self.id}")
        logger.info(f'getValidUserList_school_exclude test experiment: {testExperiment}')
        #logger.info(f'getValidUserList_school_exclude incoming list: {u_list}')

        start_time = datetime.now()

        if not self.recruitment_params.schools_exclude_constraint:
            return u_list
        
        #get list of invalid email filters
        invaild_email_filters = []

        for school in self.recruitment_params.schools_exclude.all():
            for email_filter in school.email_filter.all():
                invaild_email_filters.append(email_filter)
        
        logger.info(f'getValidUserList_school_exclude email filters: {invaild_email_filters}')

        pk_list = []

        for u in u_list:                
            pk_list.append(u.id)

        #return list of users that have email filter
        u_list_updated = User.objects.exclude(profile__email_filter__in=invaild_email_filters) \
                                     .filter(id__in=pk_list)

        logger.info(f'getValidUserList_school_exclude valid user: {u_list_updated}')
        logger.info(f'getValidUserList_school_exclude run time: {datetime.now() - start_time}')

        return list(u_list_updated)

    #return a valid subset of users who are in in the desired school
    def getValidUserList_school_include(self, u_list, testExperiment):
        logger = logging.getLogger(__name__)
        logger.info(f"getValidUserList_school_include {self.id}")
        logger.info(f'getValidUserList_school_include test experiment: {testExperiment}')
        #logger.info(f'getValidUserList_school_include incoming list: {u_list}')

        start_time = datetime.now()

        if not self.recruitment_params.schools_include_constraint:
            return u_list

        #get list of email filters
        vaild_email_filters=[]

        for school in self.recruitment_params.schools_include.all():
            for email_filter in school.email_filter.all():
                vaild_email_filters.append(email_filter)

        logger.info(f'getValidUserList_school_include email filters: {vaild_email_filters}')

        pk_list = []

        for u in u_list:                
            pk_list.append(u.id)

        #return list of users that have email filter
        u_list_updated = User.objects.filter(profile__email_filter__in=vaild_email_filters) \
                                     .filter(id__in=pk_list)

        #logger.info(f'getValidUserList_school_include valid user: {u_list_updated}')
        logger.info(f'getValidUserList_school_include run time: {datetime.now() - start_time}')

        return list(u_list_updated) 

    #return valid subset of users that are not already participating at this date and time
    def getValidUserList_date_time_overlap(self, u_list, testSession):
        logger = logging.getLogger(__name__)
        logger.info(f"getValidUserList_date_time_overlap {self.id}")

        start_time = datetime.now()

        #return u_list

        logger.info(f'getValidUserList_date_time_overlap test session: {testSession}')
        #logger.info(f'getValidUserList_date_time_overlap incoming list: {u_list}')

        #(StartDate1 <= EndDate2) and (StartDate2 <= EndDate1)
        #date range constraints for all this session's days that have time enabled
       
        # d_query = reduce(or_, ((Q(date__lte = esd.date_end) & \
        #                         Q(date_end__gte = esd.date)) for esd in self.ESD.filter(enable_time = True)))

        d_query=[]

        for esd in self.ESD.filter(enable_time = True):
            d_query.append(Q(date__lte = esd.date_end) & Q(date_end__gte = esd.date))

        #session does not have any time enabled days to test
        if len(d_query) == 0:
            logger.info("getValidUserList_date_time_overlap no date enabled sessions")
            return u_list
        
        #find overlaping session days with this session's days
        session_overlap = main.models.experiment_session_days.objects.filter(experiment_session__canceled=False)\
                                                                    .exclude(experiment_session__id = self.id)\
                                                                    .filter(enable_time = True)\
                                                                    .filter(reduce(or_,d_query))

        session_overlap = list(session_overlap)

        #add test session days in
        if testSession>0:
            test_session_overlap = main.models.experiment_session_days.objects.filter(experiment_session__id = testSession)\
                                                                              .exclude(experiment_session__id = self.id)\
                                                                              .filter(reduce(or_,d_query))\
                                                                              .filter(enable_time = True)

            test_session_overlap = list(test_session_overlap)

            for i in test_session_overlap:
                session_overlap.append(i)
                                                                   

        logger.info(f'getValidUserList_date_time_overlap session: {session_overlap}')

        #find list of users in overlapping sessions who are not eligable
        user_overlap = main.models.experiment_session_day_users.objects.filter(experiment_session_day__in = session_overlap)\
                                                                       .filter(confirmed = True)\
                                                                       .values_list("user_id",flat=True)

        logger.info(f'getValidUserList_date_time_overlap user overlap: {list(user_overlap)}')

        #remove invalid users from list
        u_list_updated = []

        for u in u_list:
            if u.id not in user_overlap:
                u_list_updated.append(u)

        #logger.info(f'getValidUserList_date_time_overlap valid user: {u_list_updated}')
        logger.info(f'getValidUserList_date_time_overlap run time: {datetime.now() - start_time}')

        return u_list_updated
        
    #return valid subset of u_list that conforms to include trait constraints
    def getValidUserList_trait_constraints(self, u_list, testExperiment):
        logger = logging.getLogger(__name__)
        logger.info("getValidUserList_trait_constraints")

        start_time = datetime.now()

        constraint_list_traits_ids = self.recruitment_params.trait_constraints.filter(include_if_in_range=True) \
                                                                              .values_list("trait__id",flat=True)

        logger.info(f'getValidUserList_trait_constraints constraint ids: {constraint_list_traits_ids}')
        trait_list = main.models.Traits.objects.filter(pk__in = constraint_list_traits_ids)
        logger.info(f'getValidUserList_trait_constraints trait list: {trait_list}')

        if len(constraint_list_traits_ids) == 0:
            return u_list
        else:
            pk_list = []

            for u in u_list:                
                pk_list.append(u.id)

            #create dictionary of target traits
            tc = {}
            for i in self.recruitment_params.trait_constraints.filter(include_if_in_range=True):
                tc[i.trait] = {"min_value":i.min_value, "max_value":i.max_value}

            #list to be returned of valid users
            valid_list_2 = []

            #subject must meet all trait requirments
            if self.recruitment_params.trait_constraints_require_all:
                #count list of users that have full trait set
                valid_list = User.objects.annotate(trait_count =  Count('profile__profile_traits__trait',filter = Q(profile__profile_traits__trait__in=trait_list)))\
                                         .filter(trait_count = len(trait_list))\
                                         .filter(pk__in = pk_list)\
                                         .prefetch_related('profile__profile_traits')

                #create new list of users that have traits within target range
                for u in valid_list:
                    valid = True

                    for i in u.profile.profile_traits.filter(trait__in = tc):
                        temp_tc = tc.get(i.trait)                        
                        
                        if i.value < temp_tc["min_value"] or i.value> temp_tc["max_value"]:
                            valid=False
                            break    

                    if valid:
                        valid_list_2.append(u)
                        
                # return list(valid_list_2)
            else:
                #subject must meet one of the trait requirments 

                #count list of users that have at least one trait in set
                valid_list = User.objects.annotate(trait_count =  Count('profile__profile_traits__trait',filter = Q(profile__profile_traits__trait__in=trait_list)))\
                                         .filter(trait_count__gte = 1)\
                                         .filter(pk__in = pk_list)\
                                         .prefetch_related('profile__profile_traits')

                for u in valid_list:
                    valid = False

                    #include if subject has one trait within specifed range
                    for i in u.profile.profile_traits.filter(trait__in = tc):
                        temp_tc = tc.get(i.trait)

                        if i.value >= temp_tc["min_value"] and i.value <= temp_tc["max_value"]:
                            valid=True
                            break                          

                    if valid:
                        valid_list_2.append(u)

            logger.info(f'getValidUserList_trait_constraints run time: {datetime.now() - start_time}')

            return list(valid_list_2)    

    #return valid subset of u_list that conforms to exclude trait constraints
    def getValidUserList_trait_constraints_exclude(self, u_list, testExperiment):
        logger = logging.getLogger(__name__)
        logger.info("getValidUserList_trait_constraints_exclude")

        start_time = datetime.now()

        constraint_list_traits_ids = self.recruitment_params.trait_constraints.filter(include_if_in_range=False) \
                                                                              .values_list("trait__id",flat=True)

        logger.info(f'getValidUserList_trait_constraints constraint ids: {constraint_list_traits_ids}')
        trait_list = main.models.Traits.objects.filter(pk__in = constraint_list_traits_ids)
        logger.info(f'getValidUserList_trait_constraints trait list: {trait_list}')

        if len(constraint_list_traits_ids) == 0:
            return u_list
        else:
            pk_list = []

            for u in u_list:                
                pk_list.append(u.id)

            #create dictionary of target traits
            tc = {}
            for i in self.recruitment_params.trait_constraints.filter(include_if_in_range=False):
                tc[i.trait] = {"min_value":i.min_value, "max_value":i.max_value}

            #list to be returned of valid users
            valid_list_2 = []

            valid_list = User.objects.filter(pk__in = pk_list)\
                                     .prefetch_related('profile__profile_traits')          

            for u in valid_list:
                valid = True

                #exclude if subject violates one of the trait exclusions
                for i in u.profile.profile_traits.filter(trait__in = tc):
                    temp_tc = tc.get(i.trait)

                    if i.value >= temp_tc["min_value"] and i.value <= temp_tc["max_value"]:
                        valid=False
                        break                          

                if valid:
                    valid_list_2.append(u)

            logger.info(f'getValidUserList_trait_constraints_exclude run time: {datetime.now() - start_time}')

            return list(valid_list_2)

    #return valid subset of users that are not already participating at this date and time
    def getValidUserList_date_time_overlap(self, u_list, testSession):
        logger = logging.getLogger(__name__)
        logger.info(f"getValidUserList_date_time_overlap {self.id}")

        start_time = datetime.now()

        #return u_list

        logger.info(f'getValidUserList_date_time_overlap test session: {testSession}')
        #logger.info(f'getValidUserList_date_time_overlap incoming list: {u_list}')

        #(StartDate1 <= EndDate2) and (StartDate2 <= EndDate1)
        #date range constraints for all this session's days that have time enabled
       
        # d_query = reduce(or_, ((Q(date__lte = esd.date_end) & \
        #                         Q(date_end__gte = esd.date)) for esd in self.ESD.filter(enable_time = True)))

        d_query=[]

        for esd in self.ESD.filter(enable_time = True):
            d_query.append(Q(date__lte = esd.date_end) & Q(date_end__gte = esd.date))

        #session does not have any time enabled days to test
        if len(d_query) == 0:
            logger.info("getValidUserList_date_time_overlap no date enabled sessions")
            return u_list
        
        #find overlaping session days with this session's days
        session_overlap = main.models.experiment_session_days.objects.filter(experiment_session__canceled=False)\
                                                                    .exclude(experiment_session__id = self.id)\
                                                                    .filter(enable_time = True)\
                                                                    .filter(reduce(or_,d_query))

        session_overlap = list(session_overlap)

        #add test session days in
        if testSession>0:
            test_session_overlap = main.models.experiment_session_days.objects.filter(experiment_session__id = testSession)\
                                                                              .exclude(experiment_session__id = self.id)\
                                                                              .filter(reduce(or_,d_query))\
                                                                              .filter(enable_time = True)

            test_session_overlap = list(test_session_overlap)

            for i in test_session_overlap:
                session_overlap.append(i)
                                                                   

        logger.info(f'getValidUserList_date_time_overlap session: {session_overlap}')

        #find list of users in overlapping sessions who are not eligable
        user_overlap = main.models.experiment_session_day_users.objects.filter(experiment_session_day__in = session_overlap)\
                                                                       .filter(confirmed = True)\
                                                                       .values_list("user_id",flat=True)

        logger.info(f'getValidUserList_date_time_overlap user overlap: {list(user_overlap)}')

        #remove invalid users from list
        u_list_updated = []

        for u in u_list:
            if u.id not in user_overlap:
                u_list_updated.append(u)

        #logger.info(f'getValidUserList_date_time_overlap valid user: {u_list_updated}')
        logger.info(f'getValidUserList_date_time_overlap run time: {datetime.now() - start_time}')

        return u_list_updated
          
    #check that users have the correct number of past or upcoming experience
    def getValidUserList_check_experience(self, u_list, testExperiment):
        logger = logging.getLogger(__name__)
        logger.info("getValidUserList_check_experience")

        start_time = datetime.now()

        if self.recruitment_params.experience_constraint:
            pk_list = []

            for u in u_list:                
                pk_list.append(u.id)

            e_min = self.recruitment_params.experience_min
            e_max = self.recruitment_params.experience_max

            if testExperiment:
                e_min -=1
                e_max -=1

            last_date = self.getLastDate()

            #return count of any session day subject attened
            #or sessions they have confirmed for in the future that have not been canceled
            valid_list = User.objects.annotate(session_count = Count('ESDU__experiment_session_day__experiment_session__experiment',
                                                                              distinct=True,
                                                                              filter = (Q(ESDU__attended = True) | 
                                                                                        (Q(ESDU__confirmed = True) & 
                                                                                            Q(ESDU__experiment_session_day__date__gte = datetime.now(pytz.UTC)) &
                                                                                            Q(ESDU__experiment_session_day__date__lte = last_date) &
                                                                                            Q(ESDU__experiment_session_day__experiment_session__canceled = False) )) & 
                                                                                        ~Q(ESDU__experiment_session_day__experiment_session = self) ))\
                                          .filter(session_count__gte=e_min)\
                                          .filter(session_count__lte=e_max)\
                                          .filter(pk__in = pk_list)
            
            #valid_user_list = []

            
            logger.info(f'getValidUserList_check_experience run time: {datetime.now() - start_time}')

            return list(valid_list)
        else:
            return u_list

    #check that users have  are not no-show blocked
    def getValidUserList_check_now_show_block(self, u_list):
        logger = logging.getLogger(__name__)
        logger.info("getValidUserList_check_now_show_block")

        no_show_blocks = main.globals.get_now_show_blocks()

        if len(no_show_blocks) == 0:
            return u_list

        valid_list=[]

        for u in u_list:
            if u not in no_show_blocks:
                valid_list.append(u)

        return valid_list
        
    #return true if all session days are complete
    def getComplete(self):
        esd_not_complete = self.ESD.filter(complete = False)

        if esd_not_complete:
            return False
        else:
            return True

    #get the number of hours until the first session starts
    def hoursUntilFirstStart(self):
        esd = self.ESD.order_by('date').first()

        return esd.hoursUntilStart() if esd else 0
    
    #number of confirmed subjects
    def getConfirmedCount(self):
        logger = logging.getLogger(__name__)
        #logger.info("Confirmed count")    
        

        esd = self.ESD.order_by('date').first()

        if esd:
            esdu_confirmed_count = main.models.experiment_session_day_users.objects.filter(experiment_session_day__id=esd.id,
                                                                                           confirmed = True)\
                                                                                    .count()
            #logger.info(esdu_confirmed_count)
            return esdu_confirmed_count
        else:
            logger.info("Confirmed count error, no session days found") 
            return 0
    
    #return true if session is full
    def getFull(self):
        logger = logging.getLogger(__name__)

        return True if self.getConfirmedCount() >= self.recruitment_params.registration_cutoff else False
    
    #return the first date of the session
    def getFirstDate(self):
        logger = logging.getLogger(__name__)
        logger.info("Get first session day date, session:" + str(self.id))

        d = self.ESD.all().order_by('date').first().date

        logger.info(d)

        return d
    
    #return the last date of the session
    def getLastDate(self):
        logger = logging.getLogger(__name__)
        logger.info("Get last session day date, session:" + str(self.id))

        d = self.ESD.all().order_by('-date').first().date

        logger.info(d)

        return d

    #return the last session day
    def getLastSessionDay(self):
        logger = logging.getLogger(__name__)
        
        d = self.ESD.all().order_by('-date').first()

        logger.info(d)

        return d

    #json sent to subject screen
    def json_subject(self, u):
        logger = logging.getLogger(__name__)
        logger.info("json subject, session:" + str(self.id))

        esdu = main.models.experiment_session_day_users.objects.filter(experiment_session_day__experiment_session__id = self.id,
                                                                       user__id = u.id)\
                                                                .order_by('experiment_session_day__date')\
                                                                .first()

        #check that other experience is not invaldating this session if not confirmed  
        user_list_valid_check = True

        if not esdu.confirmed:
            #user_list_valid = self.getValidUserList([{'id':u.id}],False,0,0,[],False)

            user_list_valid = self.getValidUserList_forward_check([{'id':u.id}],False,0,0,[],False,1)

            if not u in user_list_valid:
                user_list_valid_check=False

        #check that accepting this experiment will not invalidate other accepted experiments if not confirmed
        user_list_valid2_check=True
       
        if not esdu.confirmed:
            user_list_valid2_check = not u.profile.check_for_future_constraints(self,
                                                                                self.getFirstDate(),
                                                                                self.experiment.institution.values_list("id", flat=True),
                                                                                self.experiment.id)                  
        
        return{
            "id":self.id,                                  
            "experiment_session_days" : [{"id" : esd.id,
                                          "date" : esd.date,
                                          "date_end" : esd.date_end,
                                          "enable_time" : esd.enable_time,
                                          "length" : esd.length,
                                          "hours_until_start ": esd.hoursUntilStart(),
                                          "hours_until_start_str":  str(int(esd.hoursUntilStart())) + " hours<br>" + 
                                                                       str(int(esd.hoursUntilStart() %1 * 60)) + ' minutes' 
                                                                   if esd.hoursUntilStart() >= 1 else
                                                                    str(int(esd.hoursUntilStart() %1 * 60)) + ' minutes'   ,
                                          } for esd in self.ESD.all().annotate(first_date=models.Min('date'))
                                                                     .order_by('-first_date')
                                        ],
            "canceled":self.canceled,
            "consented" : u.profile.check_for_consent(self.consent_form),
            "confirmed" : esdu.confirmed if esdu else False,
            "consent_form":{"id":self.consent_form.id} if self.consent_form else None,
            "hours_until_first_start": self.hoursUntilFirstStart(),
            "full": self.getFull(),
            "valid" : False if not user_list_valid_check or not user_list_valid2_check else True,
        }
    
    #get session days attached to this session
    def json_esd(self,getUnConfirmed):
        return{          
            "experiment_session_days" : [esd.json(getUnConfirmed) for esd in self.ESD.all().annotate(first_date=models.Min('date'))
                                                                                           .order_by('-first_date')],
            "invitationText" : self.getInvitationEmail(),
            "confirmedEmailList" : self.getConfirmedEmailList(),
            "confirmedCount":self.getConfirmedCount(),
        }

    #get some of the json object
    def json_min(self):
        return{
            "id":self.id,
            "complete":self.getComplete(),   
            "canceled":self.canceled, 
            "creator": f"{self.creator.last_name}, {self.creator.first_name}" if self.creator else "---",                    
            "experiment_session_days" : [esd.json_min() for esd in self.ESD.all().annotate(first_date=models.Min('date'))
                                                                                 .order_by('-first_date')],
            "allow_delete": self.allowDelete(),            
        }

    #get full json object
    def json(self):
        #days_list = self.ESD.order_by("-date").prefetch_related('ESDU_b')

        return{
            "id":self.id,            
            "experiment":self.experiment.id,
            "canceled":self.canceled,
            "consent_form":self.consent_form.id if self.consent_form else None,
            "consent_form_full":self.consent_form.json() if self.consent_form else None,
            "experiment_session_days" : [esd.json(False) for esd in self.ESD.all().annotate(first_date=models.Min('date')).order_by('-first_date')],
            "invitationText" : self.getInvitationEmail(),
            "invitationRawText" : self.invitation_text,
            "cancelationText" : self.getCancelationEmail(),
            "confirmedEmailList" : self.getConfirmedEmailList(),
            "messageCount": self.experiment_session_messages_set.count(),
            "invitationCount": self.experiment_session_invitations.count(),
            "allowDelete":self.allowDelete(),
            "allowEdit":self.allowEdit(),
            "confirmedCount":self.getConfirmedCount(),
        }

#delete recruitment parameters when deleted
@receiver(post_delete, sender=experiment_sessions)
def post_delete_recruitment_params(sender, instance, *args, **kwargs):
    if instance.recruitment_params: # just in case user is not specified
        instance.recruitment_params.delete()