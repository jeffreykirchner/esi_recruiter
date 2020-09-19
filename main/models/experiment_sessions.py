from django.db import models
import logging
import traceback
from django.urls import reverse
import main
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import User
from datetime import datetime, timedelta,timezone
import pytz

from django.dispatch import receiver
from django.db.models.signals import post_delete

from django.db.models import Q,F,Value as V,Count

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
                 "user_first_name":i['user__first_name'],
                 "user_last_name":i['user__last_name'],} for i in l ]

    #build an invition email given the experiment session
    def getInvitationEmail(self):

        p = parameters.objects.get(id=1)
       
        message = ""

        message = self.experiment.invitationText
        message = message.replace("[confirmation link]",p.siteURL)
        message = message.replace("[session length]",self.getSessionDayLengthString())
        message = message.replace("[session date and time]",self.getSessionDayDateString())
        message = message.replace("[on time bonus]","$" + self.experiment.getShowUpFeeString())
        message = message.replace("[contact email]",p.labManager.email)

        return message
    
    #build an reminder email given the experiment session
    def getReminderEmail(self):

        p = parameters.objects.get(id=1)
       
        message = ""

        message = self.experiment.reminderText
        message = message.replace("[confirmation link]",p.siteURL)
        message = message.replace("[session length]",self.getSessionDayLengthString())
        message = message.replace("[session date and time]",self.getSessionDayDateString())
        message = message.replace("[on time bonus]","$" + self.experiment.getShowUpFeeString())
        message = message.replace("[contact email]",p.labManager.email)

        return message
    
    #build a cancelation email for this experiment session
    def getCancelationEmail(self):
        p = parameters.objects.get(id=1)

        message = ""

        message = p.cancelationText
        message = message.replace("[session date and time]",self.getSessionDayDateString())
        message = message.replace("[contact email]",p.labManager.email)

        return message

    #add new user to session
    def addUser(self,userID,staffUser,manuallyAdded):
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

    #do getValidUserList but in Django DB functions
    def getValidUserListDjango(self,u_list,checkAlreadyIn,testExperiment):
        logger = logging.getLogger(__name__)
        logger.info("Get valid user list for session (django DB fuctions) " + str(self))

        time_start = datetime.now()       

        es_p = self.recruitmentParams

        #table of users and institutions
        user_institution_list = experiments.objects\
                                .values(user_id=F("ES__ESD__experiment_session_day_users__user__id"),
                                        institution_id=F("institution__id"),
                                        institution_name=F("institution__name"),
                                        attended=F("ES__ESD__experiment_session_day_users__attended"),
                                        bumped=F("ES__ESD__experiment_session_day_users__bumped"),
                                        confirmed=F("ES__ESD__experiment_session_day_users__confirmed"),
                                        date = F("ES__ESD__date"))\
                                .filter(attended = True)\
                                .distinct()

        #institutions to include
        institutions_include_list = list(es_p.institutions_include.values_list('id',flat=True).distinct())
        logger.info(institutions_include_list)

        if len(institutions_include_list) > 0:
            #users that have at least one of required institutions
            user_institutions_include_list = user_institution_list.filter(institution_id__in = institutions_include_list)\
                                                                  .filter(user_id__in = [18,15])\
                                                                  .values("user_id","institution_id")\
                                                                  .distinct()                                                                                                          

            logger.info(user_institutions_include_list)

            #user must have all required institution experience
            if es_p.institutions_include_all:
                tempL = list(user_institutions_include_list)
                logger.info(tempL)

                


                user_institutions_include_list = user_institutions_include_list.values('user_id')\
                                                                               .annotate(user_id_count = Count('user_id',distinct=True))\
                                                                               .filter(user_id_count__gte = len(institutions_include_list))
                                                                               


                logger.info("Users with needed institutions, count:" + str(len(user_institutions_include_list)))                                   
                logger.info(user_institutions_include_list)

        #institutions that subject should not have done

        #experiments that subject should have done

        #experiments that subject should not have done

        time_end = datetime.now()
        time_span = time_end-time_start
        logger.info("SQL Run time: " + str(time_span.total_seconds()))

        u_list = User.objects.filter(id__in = user_institutions_include_list.values_list("user_id",flat=True))

        u_list = list(u_list)

        return u_list


    #return a list of all valid users that can participate
    #u_list confine search to list, empty for all subjects
    #checkAlreadyIn checks if a subject is already added to session
    #if testExperiment is greater than 0, use to test valid list if user were to hypothetically participate in that experiment
    def getValidUserList(self,u_list,checkAlreadyIn,testExperiment):
        logger = logging.getLogger(__name__)
        logger.info("Get valid user list for session " + str(self))

        if u_list==[]:
            u_list = User.objects.filter(is_active=True).values("id")

        es = self
        es_p = es.recruitmentParams
        id =  self.id
        p = parameters.objects.get(id=1)

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
            allow_multiple_participations_str='''
            --check that user has not already done this experiment
            NOT EXISTS(SELECT 1                                                   
                       FROM user_experiments
                       WHERE user_experiments.user_id = auth_user.id AND
                             experiment_sessions_id != '''+ str(id) + ''' AND
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
            --experiments that subject should not have done already
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
             emailFilter_include AS (SELECT email_filters_id
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
                    WHERE main_profile.emailFilter_id = emailFilter_include.email_filters_id) AND 
            '''

        #schools exclude strings
        schools_exclude_user_where_str = ""
        schools_exclude_with_str = ""
        if es_p.schools_exclude_constraint:
            schools_exclude_with_str = '''
             --subject cannot be in any of these schools
              emailFilter_exclude AS (SELECT email_filters_id
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
                    WHERE main_profile.emailFilter_id = emailFilter_exclude.email_filters_id) AND
            '''

        #list of users to search for, if empty return all valid users
        users_to_search_for=""
        user_to_search_for_list_str = ""
        if len(u_list) > 0:
            logger.info(u_list)
            user_to_search_for_list_str = "("
            for u in u_list:
                if( user_to_search_for_list_str != "("):
                    user_to_search_for_list_str += " , "

                user_to_search_for_list_str += str(u['id'])

            user_to_search_for_list_str += ")"

            users_to_search_for += 'auth_user.id IN ' + user_to_search_for_list_str + ' AND '

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
                    INNER JOIN main_experiment_session_days ON main_experiment_session_days.id  = main_experiment_session_day_users.experiment_session_day_id
                    INNER JOIN main_experiment_sessions ON main_experiment_sessions.id = main_experiment_session_days.experiment_session_id
                    WHERE ''' + users_to_search_for + '''
                        (main_experiment_session_day_users.attended = 1 OR
                        (main_experiment_session_day_users.confirmed = 1 AND 
                           main_experiment_session_days.date_end >=  CURRENT_TIMESTAMP AND
                           main_experiment_session_days.date_end <= \'''' + str(self.getLastDate()) + '''\' )) AND
                        main_experiment_sessions.id != ''' + str(id) + ''' 
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
            user_experiments AS (SELECT main_experiments.id as experiments_id,
                                            main_experiment_sessions.id as experiment_sessions_id,
                                            main_experiment_session_day_users.user_id as user_id
                            FROM main_experiments
                            INNER JOIN main_experiment_sessions ON main_experiment_sessions.experiment_id = main_experiments.id
                            INNER JOIN main_experiment_session_days ON main_experiment_session_days.experiment_session_id = main_experiment_sessions.id
                            INNER JOIN main_experiment_session_day_users ON main_experiment_session_day_users.experiment_session_day_id = main_experiment_session_days.id
                            WHERE ('''
        if testExperiment > 0:
            user_experiments_str += '''main_experiments.id = ''' + str(testExperiment) + ''' OR '''

        if len(u_list) > 0:
            user_experiments_str +='''(main_experiment_session_day_users.attended = 1 OR
                                      (main_experiment_session_day_users.confirmed = 1 AND 
                                            main_experiment_session_days.date_end >=  CURRENT_TIMESTAMP AND
                                            main_experiment_session_days.date_end <= \'''' + str(self.getLastDate()) + '''\' ))) AND
                                       main_experiment_session_day_users.user_id IN ''' + user_to_search_for_list_str +  '''),  
                '''
        else:
            user_experiments_str +='''(main_experiment_session_day_users.attended = 1 OR
                                      (main_experiment_session_day_users.confirmed = 1 AND
                                            main_experiment_session_days.date_end >=  CURRENT_TIMESTAMP AND
                                            main_experiment_session_days.date_end <= \'''' + str(self.getLastDate()) + '''\')))),
                '''

        #list of users in current session
        user_current_sesion_str = '''
            ---table of users that have been invited to the current session
            user_current_sesion AS (SELECT main_experiment_sessions.id as experiment_sessions_id,
                                        main_experiment_session_day_users.user_id as user_id
                                FROM main_experiment_sessions
                                INNER JOIN main_experiment_session_days ON main_experiment_session_days.experiment_session_id = main_experiment_sessions.id
                                INNER JOIN main_experiment_session_day_users ON main_experiment_session_day_users.experiment_session_day_id = main_experiment_session_days.id
                                WHERE main_experiment_sessions.id = ''' + str(id) + '''),
        '''  

        #list of users who are already doing an experiment during this time
        #(StartDate1 <= EndDate2) and (StartDate2 <= EndDate1)
        user_during_session_time_str = '''
            --table of users who are already doing an expeirment at this time
             user_during_session_time AS (SELECT auth_user.id as user_id
                            FROM auth_user
                            INNER JOIN main_experiment_session_day_users on main_experiment_session_day_users.user_id = auth_user.id
                            INNER JOIN main_experiment_session_days ON main_experiment_session_days.id = main_experiment_session_day_users.experiment_session_day_id
                            INNER JOIN main_experiment_sessions ON main_experiment_sessions.id = main_experiment_session_days.experiment_session_id
                            WHERE main_experiment_sessions.id != '''+ str(id) + ''' AND 
                                  main_experiment_session_day_users.confirmed = 1 AND 
                                  ('''
        tempS = ""
        for d in es.ESD.all():
            if tempS != "":
                tempS += ''' OR '''
            tempS+= '''(main_experiment_session_days.date <= \'''' + str(d.date_end) + '''\' AND \'''' + str(d.date) + '''\' <= main_experiment_session_days.date_end )'''

        user_during_session_time_str+= tempS

        user_during_session_time_str +=''' ) AND 
                                       '''

        if len(u_list) > 0:
            user_during_session_time_str+= ''' auth_user.id IN ''' + user_to_search_for_list_str + ''' AND 
                                           '''

        user_during_session_time_str += '''main_experiment_sessions.canceled = 0 
                                            ),
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
                                main_experiment_session_days.date >= \'''' + str(d) + '''\' AND
                                main_experiment_session_days.date <= CURRENT_TIMESTAMP AND
                                ''' + users_to_search_for + '''
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
                                WHERE (
            '''
            if testExperiment > 0:
                user_institutions_str += '''main_experiments.id = ''' + str(testExperiment) + ''' OR ''' 

            if len(u_list) > 0:
                user_institutions_str +='''       
                                    (main_experiment_session_day_users.attended = 1 OR
                                    (main_experiment_session_day_users.confirmed = 1 AND 
                                       main_experiment_session_days.date_end >=  CURRENT_TIMESTAMP AND
                                       main_experiment_session_days.date_end <= \'''' + str(self.getLastDate()) + '''\') AND            
                                    main_institutions.id = main_experiments_institutions.institution_id)) AND
                                    main_experiment_session_day_users.user_id IN ''' + user_to_search_for_list_str +  '''),  
                    '''
            else:
                user_institutions_str +='''
                          (main_experiment_session_day_users.attended = 1 OR
                          (main_experiment_session_day_users.confirmed = 1 AND 
                              main_experiment_session_days.date_end >=  CURRENT_TIMESTAMP AND
                              main_experiment_session_days.date_end <= \'''' + str(self.getLastDate()) + '''\') AND
                          main_institutions.id = main_experiments_institutions.institution_id))),
                    '''

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
            + user_during_session_time_str \
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

            --check user has time slot open
            NOT EXISTS(SELECT 1
                    FROM user_during_session_time
                    WHERE auth_user.id = user_during_session_time.user_id) AND

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

        return True if self.getConfirmedCount() >= self.recruitmentParams.registration_cutoff else False
    
    #return the first date of the session
    def getFirstDate(self):
        logger = logging.getLogger(__name__)
        logger.info("Get first session day date, session:" + str(self.id))

        d = self.ESD.all().order_by('date').first().date

        logger.info(d)

        return d
    
    #return the first date of the session
    def getLastDate(self):
        logger = logging.getLogger(__name__)
        logger.info("Get last session day date, session:" + str(self.id))

        d = self.ESD.all().order_by('-date').first().date

        logger.info(d)

        return d

    #json sent to subject screen
    def json_subject(self,u):
        logger = logging.getLogger(__name__)
        logger.info("json subject, session:" + str(self.id))

        esdu = main.models.experiment_session_day_users.objects.filter(experiment_session_day__experiment_session__id = self.id,
                                                                       user__id = u.id)\
                                                                .order_by('experiment_session_day__date')\
                                                                .first()

        #check that other experience is not invaldating this session if not confirmed  
        user_list_valid_check = True

        if not esdu.confirmed:
            user_list_valid = self.getValidUserList([{'id':u.id}],False,0)
            if not u in user_list_valid:
                user_list_valid_check=False

        #check that accepting this experiment will not invalidate other accepted experiments if not confirmed
        user_list_valid2_check=True
       
        if not esdu.confirmed:
            qs_attending = u.profile.sessions_upcoming(True,self.getFirstDate())

            for s in qs_attending:

                #check that session experiment is still valid
                user_list_valid3 = s.getValidUserList([{'id':u.id}],False, 0)
                if u in user_list_valid3:

                    #check that by doing this experiment it would invalidate subject from a previously accepted experiment
                    user_list_valid2 = s.getValidUserList([{'id':u.id}],False, self.experiment.id)

                    if not u in user_list_valid2:
                            user_list_valid2_check = False
                            break

                  

        return{
            "id":self.id,                                  
            "experiment_session_days" : [{"id" : esd.id,
                                          "date":esd.date,
                                          "hours_until_start": esd.hoursUntilStart(),
                                          "hours_until_start_str":  str(int(esd.hoursUntilStart())) + " hours<br>" + 
                                                                       str(int(esd.hoursUntilStart() %1 * 60)) + ' minutes' 
                                                                   if esd.hoursUntilStart() >= 1 else
                                                                    str(int(esd.hoursUntilStart() %1 * 60)) + ' minutes'   ,
                                          } for esd in self.ESD.all().annotate(first_date=models.Min('date'))
                                                                                          .order_by('-first_date')],
            "canceled":self.canceled,
            "confirmed":esdu.confirmed if esdu else False,
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
            "experiment_session_days" : [esd.json_min() for esd in self.ESD.all().annotate(first_date=models.Min('date'))
                                                                                 .order_by('-first_date')],
            "allow_delete": self.allowDelete(),            
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
            "confirmedCount":self.getConfirmedCount(),
        }

#delete recruitment parameters when deleted
@receiver(post_delete, sender=experiment_sessions)
def post_delete_recruitmentParams(sender, instance, *args, **kwargs):
    if instance.recruitmentParams: # just in case user is not specified
        instance.recruitmentParams.delete()