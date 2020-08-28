from django.db import models
import logging
import traceback
from django.urls import reverse
import main
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import User
from datetime import datetime, timedelta,timezone

from . import genders,subject_types,institutions,experiments,parameters,recruitmentParameters,parameters

#session for an experiment (could last multiple days)
class experiment_sessions(models.Model):
    experiment = models.ForeignKey(experiments,on_delete=models.CASCADE,related_name='ES')  
    showUpFee_legacy = models.DecimalField(decimal_places=6, max_digits=10,null = True) 
    canceled=models.BooleanField(default=False)

    recruitmentParams = models.ForeignKey(recruitmentParameters,on_delete=models.CASCADE,null=True)

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

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
                 "user_last_name":i['user__first_name'],
                 "user_first_name":i['user__last_name'],} for i in l ]

    #build an invitional email given the experiment session
    def getInvitationEmail(self):
       
        message = ""

        message = self.experiment.invitationText
        message = message.replace("[confirmation link]","http://www.google.com/")
        message = message.replace("[session length]",self.getSessionDayLengthString())
        message = message.replace("[session date and time]",self.getSessionDayDateString())
        message = message.replace("[on time bonus]","$" + self.experiment.getShowUpFeeString())

        return message
    
    #build a cancelation email for this experiment session
    def getCancelationEmail(self):
        p = parameters.parameters.objects.get(id=1)

        message = ""

        message = p.cancelationText
        message = message.replace("[session date and time]",self.getSessionDayDateString())

        return message

    #add new user to session
    def addUser(self,userID):
        for esd in self.ESD.all():
            esd.addUser(userID)  

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

        p = self.experiment.recruitmentParamsDefault

        tempP = recruitmentParameters()
        tempP.setup(p)
        tempP.save()

        self.recruitmentParams = tempP
        self.recruitmentParams.save()
        self.save()
        
        # self.recruitmentParams.actual_participants = p.actual_participants
        # self.recruitmentParams.registration_cutoff = p.registration_cutoff

        # for i in p.gender.all():
        #     self.recruitmentParams.gender.add(i)
        
        # for i in p.subject_type.all():
        #     self.recruitmentParams.subject_type.add(i)

        # self.recruitmentParams.experience_min=p.experience_min
        # self.recruitmentParams.experience_max=p.experience_max
        # self.recruitmentParams.experience_constraint=p.experience_constraint

        # for i in p.institutions_exclude.all():
        #     self.recruitmentParams.institutions_exclude.add(i)
        
        # for i in p.institutions_include.all():
        #     self.recruitmentParams.institutions_include.add(i)

        # for i in p.experiments_exclude.all():
        #     self.recruitmentParams.experiments_exclude.add(i)

        # for i in p.experiments_include.all():
        #     self.recruitmentParams.experiments_include.add(i)

        # self.recruitmentParams.institutions_exclude_all=p.institutions_exclude_all
        # self.recruitmentParams.institutions_include_all=p.institutions_include_all
        # self.recruitmentParams.experiments_exclude_all=p.experiments_exclude_all
        # self.recruitmentParams.experiments_include_all=p.experiments_include_all

        # self.recruitmentParams.allow_multiple_participations=p.allow_multiple_participations

        #self.recruitmentParams.save()

        return self

    #check if this session can be deleted    
    def allowDelete(self):

        ESD = self.ESD.all()    

        for e in ESD:
            if not e.allowDelete():
                return False

        return True

    #check if any of the session days are complete
    def allowEdit(self):
        ESD_complete = self.ESD.filter(complete = True)

        if len(ESD_complete) > 0:
            return False

        return True

    #return a list of all valid users that can participate
    def getValidUserList(self,u_list,checkAlreadyIn):
        logger = logging.getLogger(__name__)
        logger.info("Get valid user list for session " + str(self))

        es = self
        es_p = es.recruitmentParams
        id =  self.id
        p = parameters.parameters.objects.get(id=1)

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
        if es_p.allow_multiple_participations:
            allow_multiple_participations_str=""
        else:
            allow_multiple_participations_str='''
            --check that user has not already done this experiment
            NOT EXISTS(SELECT 1                                                   
                       FROM user_experiments
                       WHERE user_experiments.user_id = auth_user.id AND
                             user_experiments.experiments_id =''' + str(experiment_id) + ''') AND
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

            institutions_include_with_str = '''
            --institutions that a subject should have done already
            institutions_include AS (SELECT institutions_id
                                        FROM main_recruitmentparameters_institutions_include
                                        INNER JOIN main_recruitmentparameters ON main_recruitmentparameters.id = main_recruitmentparameters_institutions_include.recruitmentparameters_id
                                        INNER JOIN main_experiment_sessions ON main_experiment_sessions.recruitmentParams_id = main_recruitmentparameters.id
                                        WHERE main_experiment_sessions.id = ''' + str(id) + '''),

            --table of users that have the correct institution experience
            institutions_include_user AS (SELECT user_institutions.auth_user_id as id,
                                                count(user_institutions.auth_user_id) as institution_include_count
                                            FROM user_institutions
                                            INNER JOIN institutions_include ON institutions_include.institutions_id = user_institutions.institution_id
                                            GROUP BY user_institutions.auth_user_id
                                            HAVING institution_include_count >= '''+ str(ii_c) + '''),
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
            institutions_exclude_with_str = '''
                --institutions that should subject should not have done already
                institutions_exclude AS (SELECT institutions_id
                                            FROM main_recruitmentparameters_institutions_exclude
                                            INNER JOIN main_recruitmentparameters ON main_recruitmentparameters.id = main_recruitmentparameters_institutions_exclude.recruitmentparameters_id
                                            INNER JOIN main_experiment_sessions ON main_experiment_sessions.recruitmentParams_id = main_recruitmentparameters.id
                                            WHERE main_experiment_sessions.id = ''' + str(id) + '''), 

                --table of users that should be excluded based on past history
                institutions_exclude_user AS (SELECT user_institutions.auth_user_id as id,
                                                    count(user_institutions.auth_user_id) as institution_exclude_count
                                                FROM user_institutions
                                                INNER JOIN institutions_exclude ON institutions_exclude.institutions_id = user_institutions.institution_id
                                                GROUP BY user_institutions.auth_user_id
                                                HAVING institution_exclude_count >= '''+ str(ie_c) + '''),
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

            experiments_include_with_str = '''
            --table of experiments that a subject should have done already
            experiments_include AS (SELECT experiments_id
                                        FROM main_recruitmentparameters_experiments_include
                                        INNER JOIN main_recruitmentparameters ON main_recruitmentparameters.id = main_recruitmentparameters_experiments_include.recruitmentparameters_id
                                        INNER JOIN main_experiment_sessions ON main_experiment_sessions.recruitmentParams_id = main_recruitmentparameters.id
                                        WHERE main_experiment_sessions.id = ''' + str(id) + '''),
            

            --table of users that have the correct experiment include experience
            experiments_include_user AS(SELECT user_experiments.user_id as id,
						                       count(user_experiments.user_id) as experiment_include_count
                                        FROM user_experiments
                                        INNER JOIN experiments_include ON experiments_include.experiments_id = user_experiments.experiments_id
                                        GROUP BY user_experiments.user_id
                                        HAVING experiment_include_count >= ''' + str(ei_c) + '''),
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

            experiments_exclude_with_str = '''
            --experiments that should subject should not have done already
            experiments_exclude AS (SELECT experiments_id
                                    FROM main_recruitmentparameters_experiments_exclude
                                    INNER JOIN main_recruitmentparameters ON main_recruitmentparameters.id = main_recruitmentparameters_experiments_exclude.recruitmentparameters_id
                                    INNER JOIN main_experiment_sessions ON main_experiment_sessions.recruitmentParams_id = main_recruitmentparameters.id
                                    WHERE main_experiment_sessions.id = ''' + str(id) + '''),

            --table of users that have the correct experiment exclude experience
            experiments_exclude_user AS(SELECT user_experiments.user_id as id,
						                       count(user_experiments.user_id) as experiment_exclude_count
                                        FROM user_experiments
                                        INNER JOIN experiments_exclude ON experiments_exclude.experiments_id = user_experiments.experiments_id
                                        GROUP BY user_experiments.user_id
                                        HAVING experiment_exclude_count >= ''' + str(ee_c) + '''),
            '''


        #schools include strings
        schools_include_user_where_str = ""
        schools_include_with_str = ""
        if es_p.schools_include_constraint:
            schools_include_with_str='''
            --subject cannot have one of these email domains
             emailFilter_include AS (SELECT DISTINCT emailFilters_id
								FROM main_schools_emailFilter			
								INNER JOIN main_recruitmentparameters_schools_include ON main_recruitmentparameters_schools_include.schools_id = main_schools_emailFilter.schools_id						
								INNER JOIN main_recruitmentparameters ON main_recruitmentparameters.id = main_recruitmentparameters_schools_include.recruitmentparameters_id
                                INNER JOIN main_experiment_sessions ON main_experiment_sessions.recruitmentParams_id = main_recruitmentparameters.id
                                WHERE main_experiment_sessions.id = ''' + str(id) +  '''),
            '''

            schools_include_user_where_str='''
            --check if subject is in the required school
            EXISTS(SELECT 1                                                   
                    FROM emailFilter_include
                    WHERE main_profile.emailFilter_id = emailFilter_include.emailFilters_id) AND 
            '''

        #schools exclude strings
        schools_exclude_user_where_str = ""
        schools_exclude_with_str = ""
        if es_p.schools_exclude_constraint:
            schools_exclude_with_str = '''
             --subject cannot be in any of these schools
              emailFilter_exclude AS (SELECT DISTINCT emailFilters_id
								FROM main_schools_emailFilter			
								INNER JOIN main_recruitmentparameters_schools_exclude ON main_recruitmentparameters_schools_exclude.schools_id = main_schools_emailFilter.schools_id						
								INNER JOIN main_recruitmentparameters ON main_recruitmentparameters.id = main_recruitmentparameters_schools_exclude.recruitmentparameters_id
                                INNER JOIN main_experiment_sessions ON main_experiment_sessions.recruitmentParams_id = main_recruitmentparameters.id
                                WHERE main_experiment_sessions.id = ''' + str(id) +  '''),
            '''

            schools_exclude_user_where_str = '''
            --check if subject is in excluded school
             NOT EXISTS(SELECT 1                                                   
                    FROM emailFilter_exclude
                    WHERE main_profile.emailFilter_id = emailFilter_exclude.emailFilters_id) AND
            '''

        #experience constraints
        user_exeriments_count_str =""
        user_exeriments_count_where=""
        if es_p.experience_constraint:
            user_exeriments_count_str ='''
            --table of users that have correct number of experiment experiences
            user_experiments_count AS (SELECT auth_user.id as id,
                    count(auth_user.id) as attended_count
                    FROM auth_user
                    INNER JOIN main_experiment_session_day_users on main_experiment_session_day_users.user_id = auth_user.id
                    WHERE main_experiment_session_day_users.attended = 1  
                    GROUP BY auth_user.id
                    HAVING attended_count BETWEEN ''' + str(es_p.experience_min) + ''' AND  ''' + str(es_p.experience_max) + '''),
            '''
            
            user_exeriments_count_where = '''
            --check if user has the correct number of experiment experiences
                EXISTS(SELECT 1
                      FROM user_experiments_count
                      WHERE auth_user.id = user_experiments_count.id) AND 
            '''

        #user experiments list
        user_experiments_str = '''
            --table of users and experiments they have been in or commited to be in
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

        #list of users in current session
        user_current_sesion_str = '''
            ---table of users that have been invited to the current session
            user_current_sesion AS (SELECT DISTINCT main_experiment_sessions.id as experiment_sessions_id,
                                        main_experiment_session_day_users.user_id as user_id
                                FROM main_experiment_sessions
                                INNER JOIN main_experiment_session_days ON main_experiment_session_days.experiment_session_id = main_experiment_sessions.id
                                INNER JOIN main_experiment_session_day_users ON main_experiment_session_day_users.experiment_session_day_id = main_experiment_session_days.id
                                WHERE main_experiment_sessions.id = ''' + str(id) + '''),
        '''  

        #table of users who have no show violations
        d = datetime.now(timezone.utc) - timedelta(days=p.noShowCutoffWindow)
        no_show_str ='''
            ---table of users who have no shows over the rolling window
            now_shows AS (SELECT auth_user.id as id,
                            COUNT(auth_user.id) as no_show_count  
                            FROM auth_user
                            INNER JOIN main_experiment_session_day_users on main_experiment_session_day_users.user_id = auth_user.id
                            INNER JOIN main_experiment_session_days ON main_experiment_session_days.id = main_experiment_session_day_users.experiment_session_day_id
                            INNER JOIN main_experiment_sessions ON main_experiment_sessions.id = main_experiment_session_days.experiment_session_id
                            WHERE main_experiment_session_day_users.confirmed = 1 AND 
                                main_experiment_session_day_users.attended = 0 AND 
                                main_experiment_session_day_users.bumped = 0 AND 
                                main_experiment_session_days.date >= "''' + str(d) + '''" AND
                                main_experiment_session_days.date <= CURRENT_TIMESTAMP AND
                                main_experiment_sessions.canceled = 0
                            GROUP BY auth_user.id
                            HAVING no_show_count >= 3),
        '''                            

        #list of institions users have been in
        user_institutions_str=""
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
            logger.info(u_list)
            users_to_search_for = "("
            for u in u_list:
                if( users_to_search_for != "("):
                    users_to_search_for += " OR "

                users_to_search_for += 'auth_user.id = ' + str(u['id'])

            users_to_search_for += ") AND"
        
        #check that subject is not already invited to session
        user_not_in_session_already=""
        if checkAlreadyIn:
            user_not_in_session_already = '''
            --user is not already invited to session     
            NOT EXISTS(SELECT 1
                    FROM user_current_sesion
                    WHERE user_current_sesion.user_id = auth_user.id) AND 
            '''

        str1='''          	  									
            WITH
            --table of genders required in session
            genders_include AS (SELECT genders_id
                                FROM main_recruitmentparameters_gender
                                INNER JOIN main_recruitmentparameters ON main_recruitmentparameters.id = main_recruitmentparameters_gender.recruitmentparameters_id
                                INNER JOIN main_experiment_sessions ON main_experiment_sessions.recruitmentParams_id = main_recruitmentparameters.id
                                WHERE main_experiment_sessions.id = ''' + str(id) + '''),
        
            ''' \
            + user_institutions_str \
            + institutions_include_with_str \
            + institutions_exclude_with_str \
            + experiments_exclude_with_str \
            + experiments_include_with_str \
            + schools_include_with_str \
            + schools_exclude_with_str \
            + user_experiments_str \
            + user_current_sesion_str\
            + no_show_str\
            + user_exeriments_count_str\
            +'''
            
            --table of subject types required in session
            subject_type_include AS (SELECT subject_types_id
                                        FROM main_recruitmentparameters_subject_type
                                        INNER JOIN main_recruitmentparameters ON main_recruitmentparameters.id = main_recruitmentparameters_subject_type.recruitmentparameters_id
                                        INNER JOIN main_experiment_sessions ON main_experiment_sessions.recruitmentParams_id = main_recruitmentparameters.id
                                        WHERE main_experiment_sessions.id = ''' + str(id) + ''')

            SELECT                 		
            
            auth_user.id,
            auth_user.last_name,
            auth_user.first_name

            FROM auth_user

            INNER JOIN main_profile ON main_profile.user_id = auth_user.id

            WHERE '''\
            + institutions_exclude_user_where_str \
            + institutions_include_user_where_str \
            + experiments_exclude_user_where_str \
            + experiments_include_user_where_str \
            + schools_exclude_user_where_str \
            + schools_include_user_where_str \
            + '''
            --user's gender is on the list
            EXISTS(SELECT 1                                                   
                    FROM genders_include	
                    WHERE main_profile.gender_id = genders_include.genders_id) AND   

            --user's subject type is on the list
            EXISTS(SELECT 1                                                   
                    FROM subject_type_include	
                    WHERE main_profile.subjectType_id = subject_type_include.subject_types_id) AND 
            
            --check user for no show violation
            NOT EXISTS(SELECT 1
                    FROM now_shows
                    WHERE auth_user.id = now_shows.id) AND

            '''\
            + user_not_in_session_already \
            + user_exeriments_count_where \
            + allow_multiple_participations_str \
            + users_to_search_for \
            + '''      
            is_staff = 0 AND                                                 --subject cannot be an admin memeber
            is_active = 1  AND                                               --acount is activated
            blackballed = 0 AND                                              --subject has not been blackballed  
            main_profile.type_id = 2 AND                                     --only subjects 
            main_profile.emailConfirmed = 'yes' AND                          --the email address has been confirmed
            main_profile.paused = 0                                          --check that the subject has not paused their account
            '''

        #str1 = str1.replace("10256","%s")

        # logger.info(str)

        users = User.objects.raw(str1) #institutions_exclude_str,institutions_include_str,experiments_exclude_str,experiments_include_str

        #log sql statement
        logger.info(users)

        time_start = datetime.now()
        u_list = list(users)
        time_end = datetime.now()
        time_span = time_end-time_start

        logger.info("SQL Run time: " + str(time_span.total_seconds()))

        return u_list

    #get some of the json object
    def json_min(self):
        return{
            "id":self.id,
            "url": str(reverse('experimentSessionView',args=(self.id,))),           
            "experiment_session_days" : [esd.json_min() for esd in self.ESD.all().annotate(first_date=models.Min('date')).order_by('-first_date')],
            "allow_delete": self.allowDelete(),
        }
    
    #get session days attached to this session
    def json_esd(self,getUnConfirmed):
        return{          
            "experiment_session_days" : [esd.json(getUnConfirmed) for esd in self.ESD.all().annotate(first_date=models.Min('date')).order_by('-first_date')],
            "invitationText" : self.getInvitationEmail(),
            "confirmedEmailList" : self.getConfirmedEmailList(),
        }

    #get full json object
    def json(self):
        #days_list = self.ESD.order_by("-date").prefetch_related('experiment_session_day_users_set')

        return{
            "id":self.id,            
            "experiment":self.experiment.id,
            "canceled":self.canceled,
            "experiment_session_days" : [esd.json(False) for esd in self.ESD.all().annotate(first_date=models.Min('date')).order_by('-first_date')],
            "invitationText" : self.getInvitationEmail(),
            "cancelationText" : self.getCancelationEmail(),
            "confirmedEmailList" : self.getConfirmedEmailList(),
            "messageCount": self.experiment_session_messages_set.count(),
            "invitationCount": self.experiment_session_invitations_set.count(),
            "allowDelete":self.allowDelete(),
            "allowEdit":self.allowEdit(),
        }