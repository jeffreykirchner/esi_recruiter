from django.db import connections
from itertools import islice
from copy import deepcopy
from django.db.models import Count, F, Value
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
import copy
from . import profile
from django.utils.timezone import make_aware
import datetime
from django.conf import settings
import pytz
from django.utils.safestring import mark_safe
from django.utils.html import escape

from main.models import institutions,\
                                departments,\
                                accounts,\
                                experiments,\
                                experiment_sessions,\
                                experiment_session_days,\
                                locations,\
                                experiment_session_day_users,\
                                experiments_institutions, \
                                schools, \
                                majors, \
                                parameters, \
                                recruitmentParameters,\
                                emailFilters, \
                                profile
                        

#migrate old data base over to new database

def migrate_institutions():
    cursor = connections['old'].cursor()
    cursor.execute('''select * from institutions''')

    institutions.objects.all().delete()

    print("Migrate Institutions")

    for c in cursor.fetchall():
        id,name,archived=c
        #print(id,name)
        institution=institutions(id=id,name=name)
        institution.save()

def migrate_departments():
        cursor = connections['old'].cursor()
        cursor.execute('''select * from departments''')

        departments.objects.all().delete()

        for c in cursor.fetchall():
                id,name,charge_account,petty_cash=c
                #print(id,name)
                department=departments(id=id,name=name,charge_account=charge_account,petty_cash=petty_cash)
                department.save()

def migrate_accounts():
        cursor = connections['old'].cursor()
        cursor.execute('''select * from accounts''')

        accounts.objects.all().delete()

        print("Migrate Accounts")

        for c in cursor.fetchall():
                id,number,department_id=c
                #print(id,number,department_id)
                account=accounts()
                account.id=id
                account.number=number
                account.department_id=int(department_id)
                account.save()
        
def migrate_schools():
        print("Migrate Schools")

        schools.objects.all().delete()

        cursor = connections['old'].cursor()
        cursor.execute('''select * from schools''')               

        for c in cursor.fetchall():
                id,name,hide_school=c

                school=schools(id=id,name=name)
                school.save()

        cursor.close()

def migrate_recruitment_parameters():
        print("Start of experiments")       

        recruitmentParameters.objects.all().delete()

        migrate_experiments()

        print("Experiment recruitment parameters")
        for e in experiments.objects.all():
                p=recruitmentParameters()
                p.actual_participants = e.actual_participants_legacy
                p.registration_cutoff = e.registration_cutoff_legacy

                p.save()

                e.recruitmentParamsDefault = p
                e.save()

        print("Session recruitment parameters")
        
        for es in experiment_sessions.objects.all():
                p = es.experiment.recruitmentParamsDefault
                p.pk = None
                p.save()

                es.recruitmentParams = p
                es.save()

def migrate_experiments():      

        print("Experiment data loading")
        cursor = connections['old'].cursor()
        cursor.execute('''SELECT experiment.id,
                                 COALESCE(TRIM(title),"No Title"),
                                 COALESCE(experiment_manager,"No Manager"),
                                 COALESCE(registration_cutoff,0),
                                 COALESCE(actual_participants,actual_participants,0),
                                 COALESCE(notes," "),
                                 CASE WHEN experiment.school_id < 1 THEN 1 ELSE experiment.school_id END,
                                 COALESCE((SELECT length_of_session
                                        FROM sessions
                                        WHERE experiment_id = experiment.id
                                        LIMIT 1),
                                        0) AS length_of_session,                                 
                                 CASE WHEN NOT EXISTS(SELECT id
                                                      FROM accounts
                                                      WHERE (SELECT account_number
                                                                FROM sessions
                                                                WHERE experiment_id = experiment.id
                                                                LIMIT 1) = id ) 
                                                THEN 1 
                                                ELSE (SELECT account_number
                                                        FROM sessions
                                                        WHERE experiment_id = experiment.id
                                                        LIMIT 1)
                                                END AS account_number
                        FROM experiments AS experiment
                      ''')

        # experiment_session_users.objects.all().delete()  
        # experiment_session_days.objects.all().delete()
        # experiment_sessions.objects.all().delete()        
        experiments.objects.all().delete()

        migrate_departments()
        migrate_accounts()
        
        migrate_institutions()

        print("data loaded")       

        objs = (experiments(id=c[0],
                                title=c[1],
                                experiment_manager=c[2],
                                registration_cutoff_legacy=c[3],
                                actual_participants_legacy=c[4],
                                notes=c[5],
                                account_default_id=c[8],
                                school_id=c[6],                                
                                length_default=c[7],
                                ) for c in cursor.fetchall())

        cursor.close()

        print("data fetched")

        batch_size=500
        # print(objs)

        counter=0

        while True:
                batch = list(islice(objs, batch_size))
                if not batch:
                        break
                experiments.objects.bulk_create(batch, batch_size)
                counter+=batch_size
                print(counter)

        migrate_sessions()

        #experiment insitutions
        print("institutions")
        counter=0
        cursor2 = connections['old'].cursor()

        cursor2.execute('''SELECT *
                          FROM experiments_institutions
                          WHERE EXISTS(SELECT id
                                       FROM institutions
                                       WHERE id = institution_id) AND
                                EXISTS(SELECT id
                                       FROM experiments
                                       WHERE id = experiment_id)''')

        objs = (experiments_institutions(experiment_id=c[1],
                                        institution_id=c[0],
                                        ) for c in cursor2.fetchall())
        
        cursor2.close()

        while True:
                batch = list(islice(objs, batch_size))
                if not batch:
                        break
                experiments_institutions.objects.bulk_create(batch, batch_size)
                counter+=batch_size
                print(counter)

        # cursor = connections['old'].cursor()
        # cursor.execute('''select * from experiments''')

        # experiments.objects.all().delete()

        # for c in cursor.fetchall():
        #         id,faculty_user_id,title,experiment_manager,archived,treatment,institution_id,group_id,registration_cutoff,actual_participants,notes,created_on,last_updated,school_id=c

        #         if school_id==0:
        #                 school_id=1

        #         if not title is None:
        #                 experiment=experiments()
        #                 experiment.id=id
        #                 experiment.title=title
        #                 experiment.experiment_manager=experiment_manager
        #                 experiment.registration_cutoff=registration_cutoff
        #                 experiment.actual_participants=actual_participants
        #                 experiment.notes=notes
        #                 experiment.school_id=school_id
        #                 experiment.account_id=1
        #                 experiment.department_id=1
        #                 experiment.save()   

def migrate_locations():
        print("Migrate Locations")

        locations.objects.all().delete()

        cursor = connections['old'].cursor()
        cursor.execute('''select * from locations''')        

        for c in cursor.fetchall():
                id,name,address=c

                location=locations(id=id,name=name,address=address)
                location.save()

        cursor.close()

def migrate_majors():
        print("Migrate Majors")

        majors.objects.all().delete()

        cursor = connections['old'].cursor()
        cursor.execute('''select * from majors''')
       
        objs = (majors(id=c[0],name=c[1]) for c in cursor.fetchall())
        cursor.close()
        batch_size=999
        # print(objs)

        while True:
                batch = list(islice(objs, batch_size))
                if not batch:
                        break
                majors.objects.bulk_create(batch, batch_size)       

def migrate_subjects1():        

        # print("Migrate Subjects 1")

        #        for p in Profile.objects.filter(type = "subject"):
        #                p.user.delete()
        #                p.delete()

        # 


        # cursor = connections['old'].cursor()
        # cursor.execute('''WITH dups AS (SELECT id 
        #                                 FROM students                                                            
        #                                 WHERE id IN(SELECT s1.id
        #                                             FROM students s1,students s2
        #                                             WHERE s1.email=s2.email AND s1.id != s2.id))
        #                         select id,                               
        #                         COALESCE(first_name,"Not Listed"),
        #                         COALESCE(last_name,"Not Listed"),                                
        #                         CASE WHEN id IN (dups)                                                                                                                              
        #                                         THEN CONCAT(id,"abc@123.edu") 
        #                                         ELSE COALESCE(email,"abc@123.edu") END                                                                
        #                 from students''')

        # batch_size=50
        # counter=0

        # objs = (User(id=c[0],
        #                 password="",
        #                 username=c[3],
        #                 first_name=c[1],
        #                 last_name=c[2],
        #                 email=c[3],
        #                 is_staff=False,
        #                 is_active=False,
        #                 is_superuser=False
        #         ) for c in cursor.fetchall())
                                        
        # while True:
        #         batch = list(islice(objs, batch_size))
        #         if not batch:
        #                 break
        #         User.objects.bulk_create(batch, batch_size)
        #         counter+=batch_size
        #         print(counter)

        print("Migrate Subjects 1")

        User.objects.exclude(id = 0).delete()
        
        cursor = connections['old'].cursor()
        cursor.execute('''select id,                                
                                COALESCE(TRIM(first_name),"Not Listed"),
                                COALESCE(TRIM(last_name),"Not Listed"),
                                CASE WHEN email IS NULL OR
                                          TRIM(email) = "" OR
                                          EXISTS(SELECT id
                                                 FROM students s2
                                                 WHERE s2.email=s1.email AND s2.id != s1.id)
                                          THEN
                                          CONCAT(id,TRIM(first_name),TRIM(last_name), "@123.edu")
                                        ELSE TRIM(email) END,
                                confirmed                                
                        from students AS s1
                        ''')
        
        print("Migrate Subjects 2")        

        objs = (User(id=c[0],
                password="",
                username=c[3].lower(),
                first_name=c[1].capitalize(),
                last_name=c[2].capitalize(),
                email=c[3].lower(),
                is_staff=False,
                is_active=c[4],
                is_superuser=False
                ) for c in cursor.fetchall())

        cursor.close()

        batch_size=500
        # print(objs)

        counter=0

        while True:
                batch = list(islice(objs, batch_size))

                if not batch:
                        break

                User.objects.bulk_create(batch, batch_size)
                counter+=batch_size
                print(counter)

        migrate_subjects2()

        #python loop
        # for c in cursor.fetchall():
               
        #         print(c)               
                
        #         tempU=c[4]

        #         # if c[4].strip()=="":
        #         #         tempU=str(c[0]) + "@123.edu"

        #         if User.objects.filter(username=c[4]).exists():
        #                 tempU=str(c[0]) + c[4]

        #         u=User.objects.create_user(id=c[0],
        #                         password="",
        #                         username=tempU,
        #                         first_name=c[2],
        #                         last_name=c[3],
        #                         email=tempU,
        #                         is_staff=False,
        #                         is_active=False,
        #                         is_superuser=False) 

        #         u.profile.chapmanID = c[1]
        #         u.profile.emailConfirmed = "no"
        #         u.profile.blackballed = c[9]
        #         u.profile.gender_id = c[6]
        #         u.profile.phone = c[5]
        #         u.profile.studentWorker=c[11]
        #         u.profile.school_id=c[12]
        #         u.profile.major_id=c[8]
        #         u.profile.type="subject"
        #         u.profile.gradStudent = c[7]   

        #         u.save() 
        # 
        #                   

def migrate_subjects2():       

        migrate_majors() 

        print("migrate profiles")

        cursor2 = connections['old'].cursor()
        cursor2.execute('''select id,
                        COALESCE(TRIM(chapman_id),"Not Listed"),                       
                        COALESCE(TRIM(phone),"0"),                                
                        CASE WHEN gender = "Female" THEN 1 ELSE 2 END,
                        CASE WHEN grade = "Graduate" THEN 2 ELSE 1 END,
                        CASE WHEN NOT EXISTS(SELECT id
                                                FROM majors
                                                WHERE s1.major_id = id ) 
                                THEN 1 
                                ELSE major_id END,                                                                                               
                        COALESCE(blackballed,0),
                        COALESCE(notes,""),
                        COALESCE(is_student_worker,0),                                
                        CASE WHEN NOT EXISTS(SELECT id
                                        FROM schools
                                        WHERE s1.school_id = id ) 
                                THEN 1 
                                ELSE school_id END  
                        from students AS s1
                        ''')
        
        batch_size=500
        counter=0        


        objs = (profile(user_id = c[0],
                        chapmanID = c[1],
                        emailConfirmed = "no",
                        blackballed = c[6],
                        gender_id = c[3],
                        phone = c[2],
                        studentWorker=c[8],
                        school_id=c[9],
                        major_id=c[5],
                        type_id=2,
                        subjectType_id = c[4],
                ) for c in cursor2.fetchall())

        cursor2.close()

        batch_size=500
        # print(objs)

        counter=0

        while True:
                batch = list(islice(objs, batch_size))

                if not batch:
                        break

                profile.objects.bulk_create(batch, batch_size)
                counter+=batch_size
                print(counter)

        print("assign email filters")
        
        for p in profile.objects.all():
                p.setupEmailFilter()        

def migrate_experiments_institutions():     
        migrate_institutions()

        c1 = connections['default'].cursor()
        c1.execute('''DELETE FROM main_experiments_institution''')

        cursor = connections['old'].cursor()
        cursor.execute('''SELECT *
                          FROM experiments_institutions
                          WHERE EXISTS(SELECT id
                                        FROM institutions 
                                        WHERE institution_id=id) AND
                          EXISTS(SELECT id
                                FROM experiments 
                                WHERE experiment_id=id)''')

        print("migrate experiment institutions")
        batch_size=500
        # print(objs)

        counter=0

        objs = (experiments.institution(experiments_id=c[1],
                                        institutions_id=c[0],
                                        ) for c in cursor.fetchall())
        cursor.close()

        while True:
                batch = list(islice(objs, batch_size))
                if not batch:
                        break
                experiments.institution.objects.bulk_create(batch, batch_size)
                counter+=batch_size
                print(counter)

        # for c in cursor.fetchall():
        #         institution_id,experiment_id=c

        #         if experiments.objects.filter(id=experiment_id).exists():
                        
        #                 experiment=experiments.objects.get(id=experiment_id)

        #                 if not institutions.objects.filter(id=institution_id).exists():
        #                         institution_id=2

        #                 experiment.institution.add(institution_id)
        #                 experiment.save()

def migrate_sessions():

        #sessions
        print("Migrate Sessions")
        print("data loading")

        cursor = connections['old'].cursor()
        cursor.execute('''SELECT sessions.id,
                                 experiment_id,                                
                                 CASE WHEN NOT on_time_bonus REGEXP '^[0-9]+(\.[0-9]+)?$'  
                                        THEN 0
                                        ELSE on_time_bonus END AS on_time_bonus,
                                 cancelled                                                                  
                        FROM sessions 
                        INNER JOIN experiments ON sessions.experiment_id=experiments.id
                        WHERE EXISTS(SELECT id
                                        FROM experiments 
                                        WHERE experiment_id=id)''')
        
        experiment_sessions.objects.all().delete()        
        
        objs = (experiment_sessions(id=c[0],
                                    experiment_id=c[1],                                    
                                    showUpFee_legacy = c[2],
                                    canceled = c[3]
                                ) for c in cursor.fetchall())

        cursor.close()
        batch_size=500
        # print(objs)

        counter=0

        while True:
                batch = list(islice(objs, batch_size))

                if not batch:
                        break

                experiment_sessions.objects.bulk_create(batch, batch_size)
                counter+=batch_size
                print(counter)

        #copy show up fees into experiment
        print("show up fees")

        e_list=experiments.objects.all().prefetch_related('ES') 
       
        for e in e_list:
                if e.ES.first():
                        
                        e.showUpFee =  e.ES.first().showUpFee_legacy                        
                else:
                        e.showUpFee = 0
                
                #print("show up fee " + str(e.id) + " " + str(e.showUpFee))
                #e.save()

        experiments.objects.bulk_update(e_list,['showUpFee'])
        
       # e_list.update()
                                
        migrate_locations()

        print("session day")

        counter=0
        batch_size=500

        cursor = connections['old'].cursor()
        cursor.execute('''SELECT sessions.id,
                                 experiment_id,
                                 CASE WHEN NOT EXISTS(SELECT id
                                                      FROM locations
                                                      WHERE location_id=id) THEN 1 ELSE location_id END AS location_id,                                   
                                 date_time,
                                 length_of_session,
                                 CASE WHEN NOT EXISTS(SELECT id
                                                      FROM accounts
                                                      WHERE account_number=id) THEN 1 ELSE account_number END AS account_number,
                                 auto_reminder,
                                 opened                             
                        FROM sessions
                        INNER JOIN experiments ON sessions.experiment_id=experiments.id 
                        WHERE EXISTS(SELECT id
                                        FROM experiments 
                                        WHERE experiment_id=id)''')

        objs = (experiment_session_days(experiment_session_id = c[0],
                                        location_id = c[2],
                                        date = make_aware(c[3],pytz.timezone("america/los_angeles")),
                                        length = c[4],                                                               
                                        account_id = c[5],
                                        auto_reminder = c[6],
                                        complete = not c[7]
                                        ) for c in cursor.fetchall())       
        cursor.close()
        
        while True:
                batch = list(islice(objs, batch_size))

                if not batch:
                        break

                experiment_session_days.objects.bulk_create(batch, batch_size)
                counter+=batch_size
                print(counter)

        #check additional day       
        print("session day, multi day")

        counter=0
        batch_size=500

        cursor = connections['old'].cursor()
        cursor.execute('''SELECT sessions.id,
                                experiment_id,
                                CASE WHEN NOT EXISTS(SELECT id
                                                FROM locations
                                                WHERE location_id=id) THEN 1 ELSE location_id END AS location_id,                                   
                                date_time,
                                length_of_session,
                                CASE WHEN NOT EXISTS(SELECT id
                                                FROM accounts
                                                WHERE account_number=id) THEN 1 ELSE account_number END AS account_number,
                                auto_reminder,
                                cancelled,
                                additional_day
                        FROM sessions
                        INNER JOIN experiments ON sessions.experiment_id=experiments.id 
                        WHERE EXISTS(SELECT id
                                        FROM experiments 
                                        WHERE experiment_id=id) AND
                        additional_day != "0000-00-00 00:00:00"''')

        objs = (experiment_session_days(experiment_session_id=c[0],
                                        location_id=c[2],
                                        date=make_aware(c[8],pytz.timezone("america/los_angeles")),
                                        length=c[4],                                                               
                                        account_id=c[5],
                                        auto_reminder = c[6]
                                        ) for c in cursor.fetchall())       

        cursor.close()

        while True:
                batch = list(islice(objs, batch_size))

                if not batch:
                        break

                experiment_session_days.objects.bulk_create(batch, batch_size)
                counter+=batch_size
                print(counter)        

                
        # experiment_session_days.objects.all().delete()


        # for c in cursor.fetchall():               
        #         id,experiment_id,location_id,date_time,length_of_session,on_time_bonus,opened,canceled,additional_day,created_on,last_updated,department_id,account_number,school_id,auto_reminder=c
                
        #         e=experiments.objects.get(id=experiment_id)                       

        #         session=experiment_sessions(id=id,experiment_id=experiment_id)
        #         session.save()

        #         if not departments.objects.filter(id=department_id).exists():
        #                 department_id = 2
                
        #         if not accounts.objects.filter(id=account_number).exists():
        #                 account_number = 1
                
        #         e.account_default_id=account_number

        #         session_day=experiment_session_days(experiment_session_id=id,
        #                                                 location_id=location_id,
        #                                                 registration_cutoff=e.registration_cutoff_default,
        #                                                 actual_participants=e.actual_participants_default,
        #                                                 date=date_time,
        #                                                 length=length_of_session,                                                               
        #                                                 account_id=account_number,
        #                                                 auto_reminder = auto_reminder,
        #                                                 canceled = canceled)
                
        #         session_day.save()

        #         if not additional_day is None:
        #                 session_day2=experiment_session_days(experiment_session_id=id,
        #                                                         location_id=location_id,
        #                                                         registration_cutoff=e.registration_cutoff_default,
        #                                                         actual_participants=e.actual_participants_default,
        #                                                         date=additional_day,
        #                                                         length=length_of_session,                                                                        
        #                                                         account_id=account_number,
        #                                                         auto_reminder = auto_reminder,
        #                                                         canceled = canceled)
        #                 session_day2.save()
                
        #         e.save()
        #         print(id)

# def migrate_session_users1():
#         print("load data")

#         cursor = connections['old'].cursor()
#         cursor.execute('''SELECT id,
#                                  session_id,
#                                  student_id 
#                           FROM sessions_students 
#                           WHERE EXISTS(SELECT id 
#                                        FROM sessions 
#                                        WHERE session_id = id) AND 
#                                 EXISTS(SELECT id 
#                                        FROM students 
#                                        WHERE student_id = id)''')       
        
#         experiment_session_users.objects.all().delete()       

#         objs = (experiment_session_users(id=c[0],
#                                          experiment_session_id=c[1],
#                                          user_id=c[2]) for c in cursor.fetchall())
        
#         print("data loaded")

#         batch_size=150        

#         counter=0

#         while True:
#                 batch = list(islice(objs, batch_size))
#                 if not batch:
#                         break
#                 experiment_session_users.objects.bulk_create(batch,batch_size)

#                 counter+=batch_size
#                 print(counter)
        
        # for c in cursor.fetchall():
        #         id,session_id,student_id,experiment_id,confirmed,denied,attended,confirmation_hash,denial_hash,ontime_earnings,participation_earnings,is_signed_for,is_multi_session_invitation,created_on,signed_fingerprint,recruit_fingerprint,invite_expired=c                       

        #         s=experiment_sessions.objects.get(id=session_id)
        #         u=User.objects.get(id=student_id)

def migrate_session_users2():
        print("session user day")

        experiment_session_day_users.objects.all().delete()

        cursor = connections['old'].cursor()
        cursor.execute('''SELECT CASE WHEN NOT ontime_earnings REGEXP '^[0-9]+(\.[0-9]+)?$'  
                                        THEN 0
                                        ELSE COALESCE(ontime_earnings,0) END,
                                  CASE WHEN NOT participation_earnings REGEXP '^[0-9]+(\.[0-9]+)?$'
                                        THEN 0
                                        ELSE COALESCE(participation_earnings,0) END,                                  
                                  COALESCE(attended,0),
                                  COALESCE(bumped,0),                                  
                                  COALESCE(confirmed,0),
                                  COALESCE(is_multi_session_invitation,0),
                                  student_id,
                                  session_id                         
                            FROM sessions_students ss_main
                            WHERE EXISTS(SELECT id 
                                       FROM sessions 
                                       WHERE session_id = id) AND 
                                  EXISTS(SELECT id 
                                       FROM students 
                                       WHERE student_id = id) AND
                                  NOT EXISTS(SELECT id as this_id,
                                                    student_id,
                                                    session_id
                                        FROM sessions_students ss_local
                                        WHERE ss_local.id != ss_main.id AND
                                              ss_local.student_id = ss_main.student_id AND
                                              ss_local.session_id = ss_main.session_id)                                                 
                                       ''')                                         

        objs = (experiment_session_day_users(show_up_fee=c[0],
                                                earnings=c[1],                                               
                                                attended=c[2],
                                                bumped=c[3],                                                
                                                confirmed=c[4],                                         
                                                multi_day_legacy = c[5],
                                                user_id=c[6],
                                                experiment_session_legacy_id = c[7]) for c in cursor.fetchall())
        
        cursor.close()

        print("data loaded")

        batch_size=500        

        counter=0

        while True:
                batch = list(islice(objs, batch_size))
                if not batch:
                        break
                experiment_session_day_users.objects.bulk_create(batch,batch_size)

                counter+=batch_size
                print(counter)

def migrate_session_users4():
        print("handle duplicate sessions day users")

        cursor = connections['old'].cursor()
        cursor.execute('''
        SELECT CASE WHEN NOT ontime_earnings REGEXP '^[0-9]+(\.[0-9]+)?$'  
                                        THEN 0
                                        ELSE COALESCE(ontime_earnings,0) END,
                                  CASE WHEN NOT participation_earnings REGEXP '^[0-9]+(\.[0-9]+)?$'
                                        THEN 0
                                        ELSE COALESCE(participation_earnings,0) END,                                  
                                  COALESCE(attended,0),
                                  COALESCE(bumped,0),                                  
                                  COALESCE(confirmed,0),
                                  COALESCE(is_multi_session_invitation,0),
                                  student_id,
                                  session_id                         
                            FROM sessions_students ss_main
                            WHERE EXISTS(SELECT id 
                                       FROM sessions 
                                       WHERE session_id = id) AND 
                                  EXISTS(SELECT id 
                                       FROM students 
                                       WHERE student_id = id) AND
                                  EXISTS(SELECT id as this_id,
                                                    student_id,
                                                    session_id
                                        FROM sessions_students ss_local
                                        WHERE ss_local.id != ss_main.id AND
                                              ss_local.student_id = ss_main.student_id AND
                                              ss_local.session_id = ss_main.session_id)  AND
                                  (ontime_earnings > 0 OR participation_earnings > 0)                                                
                                       ''')                                       

        objs = (experiment_session_day_users(show_up_fee=c[0],
                                                earnings=c[1],                                               
                                                attended=c[2],
                                                bumped=c[3],                                                
                                                confirmed=c[4],                                         
                                                multi_day_legacy = c[5],
                                                user_id=c[6],
                                                experiment_session_legacy_id = c[7]) for c in cursor.fetchall())
        
        cursor.close()
        print("data loaded")

        batch_size=500        

        counter=0

        while True:
                batch = list(islice(objs, batch_size))
                if not batch:
                        break
                experiment_session_day_users.objects.bulk_create(batch,batch_size)

                counter+=batch_size
                print(counter)

def migrate_session_users3():

        
        print("session user day to session day")

        cursorMSU31 = connections['default'].cursor()
        cursorMSU31.execute('''                                
                          UPDATE main_experiment_session_day_users		    		                
                                SET experiment_session_day_id = 
                                        (SELECT id 
                                                FROM main_experiment_session_days                                                        
                                                WHERE experiment_session_legacy_id = experiment_session_id        
                                                ORDER BY date
                                                LIMIT 1)                                
                        ''')
        cursorMSU31.close()
        #experiment_session_users_day.objects.all().update(experiment_session_day= F('experiment_session_user.experiment_session.experiment_session_days_set.first()'))

        # for sud in experiment_session_users_day.objects.all():                
        #         sud.experiment_session_day=sud.experiment_session_user.experiment_session.experiment_session_days_set.order_by('date').all()[0]

        #         if sud.multi_day_legacy:
        #                 sudNew=deepcopy(sud)
        #                 sudNew.id=None
        #                 sudNew.multi_day_legacy=False
        #                 sud.experiment_session_day=sud.experiment_session_user.experiment_session.experiment_session_days_set.order_by('date').all()[1]
        #                 sudNew.save()

        #         sud.save()
        #         print(sud.id)

def migrate_parameters():
        print("migrate parameters")

        parameters.objects.all().delete()

        #invitation text
        cursorMP1 = connections['old'].cursor()
        cursorMP1.execute('''select body,subject from boilerplates where id = 1 limit 1''')

        p = parameters()
        p.id=1

        for c in cursorMP1.fetchall():
                #invitationText = c[0]
                p.invitationText = c[0]
                p.invitationTextSubject = c[1]

        #cancelation text
        cursorMP2 = connections['old'].cursor()
        cursorMP2.execute('''select body,subject from boilerplates where id = 3 limit 1''')

        for c in cursorMP2.fetchall():
                #invitationText = c[0]
                p.cancelationText = c[0]    
                p.cancelationTextSubject = c[1]         

        #consent form
        cursorMP3 = connections['old'].cursor()
        cursorMP3.execute('''select value from ui_templates where id = 3 limit 1''')

        for c in cursorMP3.fetchall():
                p.consentForm = c[0]
 
        p.save()
