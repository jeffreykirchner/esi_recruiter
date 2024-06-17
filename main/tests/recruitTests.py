from django.test import TestCase

from django.contrib.auth.models import User
from main.views.registration import profileCreateUser
from main.models import Genders,Experiments,subject_types,AccountTypes,Majors,\
                        parameters,Accounts,Departments,locations,Institutions,schools,EmailFilters,\
                        ExperimentSessionDayUsers,Traits,Recruitment_parameters_trait_constraint,profile_trait
from main.views.staff.experiment_search_view import createExperimentBlank
from main.views.staff.experiment_view import addSessionBlank
from main.views.staff.experiment_session_view import changeConfirmationStatus,updateSessionDay,cancelSession
from main.views.subject.subject_home import acceptInvitation,cancelAcceptInvitation
from main.views.staff.experiment_session_run_view import attendSubject,bumpSubject,noShowSubject,completeSession

from datetime import datetime, timedelta
import pytz
import logging
from django.db.models import Q, F
import json
import sys


# Create your tests here.
#test gender
class GenderTestCase(TestCase):
    staff_u=None
    p=None
    d_now = None      #date time now
    l1=None           #locations
    l2=None
    account1=None     #accounts 

    def setUp(self):
        sys._called_from_test = True
        logger = logging.getLogger(__name__)

        self.p = parameters()
        self.p.save()
        
        d = Departments(name="d",charge_account="ca",petty_cash="0")
        d.save()

        self.account1 = Accounts(name="a",number="1.0",department=d)
        self.account1.save()

        self.l1=Locations(name="l",address="room")
        self.l1.save()

        i1=Institutions(name="one")
        i1.save()
        i2=Institutions(name="two")
        i2.save()
        i3=Institutions(name="three")
        i3.save()

        s=schools.objects.get(id=1)
        s.email_filter.set(EmailFilters.objects.all())

        #staff user
        user_name = "s1@chapman.edu"
        temp_st =  subject_types.objects.get(id=3)
        self.staff_u = profileCreateUser(user_name,user_name,"zxcvb1234asdf","first","last","123456",\
                            Genders.objects.first(),"7145551234",Majors.objects.first(),\
                            temp_st,False,True,AccountTypes.objects.get(id=1))
        self.staff_u.is_staff=True
        self.staff_u.save()

        self.p.labManager=self.staff_u
        self.p.save()

        #create 4 gendered users
        for g in Genders.objects.all():
            user_name = "g"+str(g.id)+"@chapman.edu"

            u = profileCreateUser(user_name,user_name,"zxcvb1234asdf","first","last","123456",\
                          Genders.objects.get(id=g.id),"7145551234",Majors.objects.first(),\
                          subject_types.objects.get(id=1),False,True,AccountTypes.objects.get(id=2))
            
            logger.info(u)

            u.is_active = True
            u.profile.email_confirmed = 'yes'

            u.profile.save()
            u.save()

            u.profile.setup_email_filter()
        
        e = createExperimentBlank()
        e.institution.set(Institutions.objects.filter(name="one"))
        e.save()
    
    def testWomenOnly(self):
        """Test only females are recruited""" 
        logger = logging.getLogger(__name__)
        
        e=Experiments.objects.first()

        #women only test
        es_women_only = addSessionBlank(e)    
        es_women_only.recruitment_params.reset_settings()
        es_women_only.recruitment_params.gender.set(Genders.objects.filter(name="Female"))
        es_women_only.recruitment_params.subject_type.set(subject_types.objects.filter(id=1))
        esd1 = es_women_only.ESD.first()
       
        u_list = es_women_only.getValidUserList_forward_check([],True,0,0,[],False,10)
        c=len(u_list)

        self.assertEqual(c, len(Genders.objects.filter(name="Female")))

        #try add to session       
       

    def testAll(self):
        """Test all genders are recruited""" 

        e=Experiments.objects.first()

        es_all = addSessionBlank(e)    
        es_all.recruitment_params.reset_settings()
        es_all.recruitment_params.gender.set(Genders.objects.all())
        es_all.recruitment_params.subject_type.set(subject_types.objects.filter(id=1))

        u_list = es_all.getValidUserList_forward_check([],True,0,0,[],False,10)
        c=len(u_list)
               
        self.assertEqual(c, len(Genders.objects.all()))

#test subject types
class subjectTypeTestCase(TestCase):
    def setUp(self):
        sys._called_from_test = True

        logger = logging.getLogger(__name__)

        p = parameters()
        p.save()
        
        d = Departments(name="d",charge_account="ca",petty_cash="0")
        d.save()

        a = Accounts(name="a",number="1.0",department=d)
        a.save()

        l=Locations(name="l",address="room")
        l.save()

        i1=Institutions(name="one")
        i1.save()
        i2=Institutions(name="two")
        i2.save()
        i3=Institutions(name="three")
        i3.save()

        s=schools.objects.first()
        s.email_filter.set(EmailFilters.objects.all())
        

        #create 5 subjects, 3 undergrad two graduates
        for g in range(5):
            user_name = "g"+str(g)+"@chapman.edu"

            temp_st=""
            if g<=2:
                temp_st =  subject_types.objects.get(id=1)
            else:
                temp_st =  subject_types.objects.get(id=2)

            u = profileCreateUser(user_name,user_name,"zxcvb1234asdf","first","last","123456",\
                          Genders.objects.first(),"7145551234",Majors.objects.first(),\
                          temp_st,False,True,AccountTypes.objects.get(id=2))
            
            logger.info(u)

            u.is_active = True
            u.profile.email_confirmed = 'yes'

            u.profile.save()
            u.save()

            u.profile.setup_email_filter()
        
        e = createExperimentBlank()
        e.institution.set(Institutions.objects.filter(name="one"))
        e.save()
    
    #undergrad only
    def testSubjectTypeUndergraduate(self):
        """Test subject type undergraduate""" 
        logger = logging.getLogger(__name__)
        
        e=Experiments.objects.first()

        es = addSessionBlank(e)    
        es.recruitment_params.reset_settings()
        es.recruitment_params.gender.set(Genders.objects.all())
        es.recruitment_params.subject_type.set(subject_types.objects.filter(id=1))
       
        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)
        c=len(u_list)

        self.assertEqual(c, len(User.objects.filter(profile__subject_type=subject_types.objects.get(id=1)))) 

    #get all types
    def testSubjectTypeAll(self):
        """Test subject type all""" 
        logger = logging.getLogger(__name__)
        
        e=Experiments.objects.first() 

        es = addSessionBlank(e)    
        es.recruitment_params.reset_settings()
        es.recruitment_params.gender.set(Genders.objects.all())
        es.recruitment_params.subject_type.set(subject_types.objects.all())
       
        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)
        c=len(u_list)

        self.assertEqual(c, len(User.objects.all()))

#test recruitment parameters
class recruitTestCase(TestCase):
    e1 = None         #experiments
    e2 = None
    user_list=[]      #list of user
    d_now = None      #date time now
    l1=None           #locations
    l2=None
    account1=None     #accounts   
    p=None            #parameters
    staff_u=None      #staff user
    
    def setUp(self):
        
        sys._called_from_test = True

        logger = logging.getLogger(__name__)

        self.p = parameters()
        self.p.save()
        
        d = Departments(name="d",charge_account="ca",petty_cash="0")
        d.save()

        self.account1 = Accounts(name="a",number="1.0",department=d)
        self.account1.save()

        self.l1=Locations(name="room1",address="room1")
        self.l1.save()
        self.l2=Locations(name="room2",address="room2")
        self.l2.save()

        i1=Institutions(name="one")
        i1.save()
        i2=Institutions(name="two")
        i2.save()
        i3=Institutions(name="three")
        i3.save()

        s=schools.objects.first()
        s.email_filter.set(EmailFilters.objects.all())

        #staff user
        user_name = "s1@chapman.edu"
        temp_st =  subject_types.objects.get(id=3)
        self.staff_u = profileCreateUser(user_name,user_name,"zxcvb1234asdf","first","last","123456",\
                          Genders.objects.first(),"7145551234",Majors.objects.first(),\
                          temp_st,False,True,AccountTypes.objects.get(id=1))
        self.staff_u.is_staff=True
        self.staff_u.save()
        
        self.p.labManager=self.staff_u
        self.p.save()

        self.user_list=[]

        #create 7 subjects
        for g in range(8):
            user_name = "g"+str(g)+"@chapman.edu"
            temp_st =  subject_types.objects.get(id=1)

            u = profileCreateUser(user_name,user_name,"zxcvb1234asdf","first","last","123456",\
                          Genders.objects.first(),"7145551234",Majors.objects.first(),\
                          temp_st,False,True,AccountTypes.objects.get(id=2))
            
            logger.info(f'{u} {u.id}')

            u.is_active = True
            u.profile.email_confirmed = 'yes'
            u.profile.paused = False           

            u.profile.setup_email_filter()

            u.profile.save()
            u.save()

            self.user_list.append(u)
        
        logger.info(self.user_list)

        self.d_now = datetime.now(pytz.utc)
        d_now_plus_one = self.d_now + timedelta(days=1)
        d_now_plus_two = self.d_now + timedelta(days=2)
        
        #setup experiment with one session two subjects, one confirmed, +1 day
        self.e1 = createExperimentBlank()
        self.e1.institution.set(Institutions.objects.filter(name="one"))
        self.e1.save()

        es1 = addSessionBlank(self.e1)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.registration_cutoff = 5
        es1.recruitment_params.save()
        es1.save()
        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        temp_u = self.user_list[1]
        es1.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        r=json.loads(changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},es1.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        temp_u = self.user_list[2]
        es1.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        r=json.loads(changeConfirmationStatus({"userId":temp_u.id,"confirmed":"unconfirm","actionAll":"false","esduId":temp_esdu.id},es1.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #setup experiment with one session three subjects, one confirmed, +2 day
        self.e2 = createExperimentBlank()
        self.e2.institution.set(Institutions.objects.filter(Q(name="one") | Q(name="three")))
        self.e2.save()

        es1 = addSessionBlank(self.e2)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.registration_cutoff = 5
        es1.recruitment_params.save()
        es1.save()
        logger.info(f'Session 1 id {es1.id}')
        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': str(esd1.id), 'formData': {'location': str(self.l1.id),'date': d_now_plus_two.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        temp_u = self.user_list[3]
        es1.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        r=json.loads(changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},es1.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        temp_u = self.user_list[4]
        es1.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        r=json.loads(changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},es1.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        temp_u = self.user_list[5]
        es1.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        r=json.loads(changeConfirmationStatus({"userId":temp_u.id,"confirmed":"unconfirm","actionAll":"false","esduId":temp_esdu.id},es1.id,False).content.decode("UTF-8"))  
        self.assertEqual(r['status'],"success")

        # #add overlapping session in another room
        es1 = addSessionBlank(self.e2)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.registration_cutoff = 5
        es1.recruitment_params.save()
        es1.save()
        logger.info(f'Session 2 id {es1.id}')
        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l2.id),'date': d_now_plus_two.strftime("%Y-%m-%dT") + '16:30','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}   
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        temp_u = self.user_list[6]
        es1.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        r = json.loads(changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},es1.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #3rd session later 1 player
        es1 = addSessionBlank(self.e2)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.registration_cutoff = 5
        es1.recruitment_params.save()
        es1.save()
        logger.info(f'Session 3 id {es1.id}')
        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_two.strftime("%Y-%m-%dT") + '18:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}   
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        temp_u = self.user_list[7]
        es1.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        r = json.loads(changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},es1.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")
    
        #subject g0 is unassinged

    #constraint disabled
    def testExperienceCountOff(self):
        """Test experience count off""" 
        logger = logging.getLogger(__name__)

        e=self.e2
        es=self.e2.ES.first()

        es.recruitment_params.experience_constraint=False
        es.recruitment_params.save()

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        e_users = ExperimentSessionDayUsers.objects.filter(experiment_session_day__experiment_session__experiment__id = e.id,
                                                              confirmed=True, 
                                                              bumped=False,
                                                              experiment_session_day__date__lte = es.getFirstDate())\
                                               .values_list("user__id",flat = True)
        e_users=list(User.objects.filter(id__in = e_users))

        logger.info("Confirmed users from experiment:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users except those already in this experiment are eligable
        for u in e_users:
            self.assertNotIn(u, u_list) 

    #no experience
    def testExperienceCountNoExperience(self):
        """Test experience count no experienece only""" 
        logger = logging.getLogger(__name__)

        e=self.e2
        es=self.e2.ES.first()

        es.recruitment_params.experience_constraint=True
        es.recruitment_params.experience_min = 0
        es.recruitment_params.experience_max = 0
        es.recruitment_params.save()

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[2])
        # e_users.append(self.user_list[7]) already confirmed for future session

        logger.info("Users not confirmed for experiment with no experience:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users except those already in this experiment are eligable, but have no other experience or upcoming
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #one or more experiments
    def testExperienceCountOnePlus(self):
        """Test experience count 1+ experience""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        esd1.ESDU_b.all().update(confirmed=False)
        #r = json.loads(cancelAcceptInvitation({"id":es.id},self.user_list[1]).content.decode("UTF-8"))

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        e=self.e2
        es=self.e2.ES.first()

        #esdu = esd1.ESDU_b.all().filter(user__username="g1@chapman.edu").first()

        #logger.info("here:" + str(esdu.attended))

        es.recruitment_params.experience_constraint=True
        es.recruitment_params.experience_min = 1
        es.recruitment_params.experience_max = 1000
        es.recruitment_params.save()

        e_users = []
        e_users.append(self.user_list[1])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Users not confirmed for experiment with 1 experience:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #one or more experiments canceled experiment in past
    def testExperienceCountOnePlusCanceledPast(self):
        """Test experience count 1+ experience canceled experiment past""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        esd1.ESDU_b.all().update(confirmed=False)
        # r = json.loads(cancelAcceptInvitation({"id":es.id},self.user_list[1]).content.decode("UTF-8"))
        # self.assertFalse(r['failed'])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)

        cancelSession({},es.id)
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        e=self.e2
        es=self.e2.ES.first()

        #esdu = esd1.ESDU_b.all().filter(user__username="g1@chapman.edu").first()

        #logger.info("here:" + str(esdu.attended))

        es.recruitment_params.experience_constraint=True
        es.recruitment_params.experience_min = 1
        es.recruitment_params.experience_max = 1000
        es.recruitment_params.save()

        e_users = [self.user_list[1]]
       
        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Users not confirmed for experiment with 1 experience:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)
    
    #one or more experiments canceled experiment in future
    def testExperienceCountOnePlusCanceledFuture(self):
        """Test experience count 1+ experience canceled experiment future""" 
        logger = logging.getLogger(__name__)

        d_now_plus_one = self.d_now + timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        esd1.ESDU_b.all().update(confirmed=False)
        # r = json.loads(cancelAcceptInvitation({"id":es.id},self.user_list[1]).content.decode("UTF-8"))
        # self.assertFalse(r['failed'])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=False,attended=False)

        cancelSession({},es.id)
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        e=self.e2
        es=self.e2.ES.first()

        #esdu = esd1.ESDU_b.all().filter(user__username="g1@chapman.edu").first()

        #logger.info("here:" + str(esdu.attended))

        es.recruitment_params.experience_constraint=True
        es.recruitment_params.experience_min = 1
        es.recruitment_params.experience_max = 1000
        es.recruitment_params.save()

        e_users = [self.user_list[1]]
       
        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Users not confirmed for experiment with 1 experience:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #no shows
    def testNoShowViolations(self):
        """Test no show violations""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        esd1.ESDU_b.all().update(confirmed=False)
        # r = json.loads(cancelAcceptInvitation({"id":es.id},self.user_list[1]).content.decode("UTF-8"))
        # self.assertFalse(r['failed'])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esdu = esd1.ESDU_b.all().filter(user=self.user_list[1]).first()
        logger.info("here:" + str(esdu.attended) + " " + str(esdu.confirmed))

        e=self.e2
        es=self.e2.ES.first()

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[2])

        self.p.noShowCutoff = 1
        self.p.save()

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Users that do not have 1 no show within last 90 days:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #no shows in canceled experiment
    def testNoShowViolationsCanceled(self):
        """Test no show violation for canceled experiment""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        esd1.ESDU_b.all().update(confirmed=False)
        # r = json.loads(cancelAcceptInvitation({"id":es.id},self.user_list[1]).content.decode("UTF-8"))
        # self.assertFalse(r['failed'])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)
       
        cancelSession({},es.id)
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        # esdu = esd1.ESDU_b.all().filter(user=self.user_list[1]).first()
        # logger.info("here:" + str(esdu.attended) + " " + str(esdu.confirmed))

        e=self.e2
        es=self.e2.ES.first()

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[1])
        e_users.append(self.user_list[2])
       

        self.p.noShowCutoff = 1
        self.p.save()

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Users that do not have 1 no show within last 90 days:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #recruit subjects with one required institution
    def testOneInstitutionRequired(self):
        """Test one institution required""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        esd1.ESDU_b.all().update(confirmed=False)
        # r = json.loads(cancelAcceptInvitation({"id":es.id},self.user_list[1]).content.decode("UTF-8"))
        # self.assertFalse(r['failed'])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)
       
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        # esdu = esd1.ESDU_b.all().filter(user=self.user_list[1]).first()
        # logger.info("here:" + str(esdu.attended) + " " + str(esdu.confirmed))

        e=self.e2
        es=self.e2.ES.first()

        es.recruitment_params.institutions_include.set(Institutions.objects.filter(name="one"))
        es.recruitment_params.save()

        e_users = []
        e_users.append(self.user_list[1])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Users that done institution one:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #recruit subjects with multiple institution requirments, must be in all
    def testTwoInstitutionRequiredAll(self):
        """Test two institutions required, must be in all""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)
        d_now_plus_one = self.d_now + timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        #setup experiment 1, insitution "one"
        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        esd1.ESDU_b.all().update(confirmed=False)
        # r = json.loads(cancelAcceptInvitation({"id":es.id},self.user_list[1]).content.decode("UTF-8"))
        # self.assertFalse(r['failed'])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)

        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #setup experiment 2 institution "one" and "three"
        e=self.e2
        es=self.e2.ES.first()
        esd1 = es.ESD.first()

        #esd1.ESDU_b.all().update(confirmed=False)
        #cancel all
        for i in e.ES.all():
            for j in i.ESD.all():
                for k in j.ESDU_b.all():
                    k.confirmed=False
                    k.save()

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[3]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[4]).update(confirmed=True,attended=True)  
        esd1.ESDU_b.all().filter(user=self.user_list[5]).update(confirmed=True,bumped=True)     
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #test experiment
        e3 = createExperimentBlank()
        e3.institution.set(Institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.institutions_include.set(Institutions.objects.filter(Q(name="one") | Q(name="three")))

        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")
        
        # esd1 = es1.ESD.first()

        e_users = []
        e_users.append(self.user_list[3])
        e_users.append(self.user_list[4])

        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Users that done institution one and three:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #recruit subjects with multiple institution requirments, must be in one plus
    def testTwoInstitutionRequiredOnePlus(self):
        """Test two institutions required, must be in one or more""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)
        d_now_plus_one = self.d_now + timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        #setup experiment 1, insitution "one"
        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        esd1.ESDU_b.all().update(confirmed=False)
        # r = json.loads(cancelAcceptInvitation({"id":es.id},self.user_list[1]).content.decode("UTF-8"))
        # self.assertFalse(r['failed'])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        e.institution.set(Institutions.objects.filter(name="one"))

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)

        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #setup experiment 2 institution "one" and "three"
        e=self.e2
        es=self.e2.ES.first()
        esd1 = es.ESD.first()

         #cancel all
        for i in e.ES.all():
            for j in i.ESD.all():
                for k in j.ESDU_b.all():
                    k.confirmed=False
                    k.save()

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[3]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[4]).update(confirmed=True,attended=True)  
        esd1.ESDU_b.all().filter(user=self.user_list[5]).update(confirmed=True,bumped=True)     
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #test experiment
        e3 = createExperimentBlank()
        e3.institution.set(Institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.institutions_include.set(Institutions.objects.filter(Q(name="one") | Q(name="three")))
        es1.recruitment_params.institutions_include_all=False

        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")
        
        # esd1 = es1.ESD.first()

        e_users = []
        e_users.append(self.user_list[1])
        e_users.append(self.user_list[3])
        e_users.append(self.user_list[4])

        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Users that done institution one and three:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #recruit subjects with multiple required institution canceled session
    def testTwoInstitutionRequiredCanceled(self):
        """Test two institutions required session canceled""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)
        d_now_plus_one = self.d_now + timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        #setup experiment 1, insitution "one"
        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        esd1.ESDU_b.all().update(confirmed=False)
        # r = json.loads(cancelAcceptInvitation({"id":es.id},self.user_list[1]).content.decode("UTF-8"))
        # self.assertFalse(r['failed'])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)

        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #setup experiment 2 institution "one" and "three"
        e=self.e2
        es=self.e2.ES.first()
        esd1 = es.ESD.first()

         #cancel all
        for i in e.ES.all():
            for j in i.ESD.all():
                for k in j.ESDU_b.all():
                    k.confirmed=False
                    k.save()

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[3]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[4]).update(confirmed=True,attended=True)  
        esd1.ESDU_b.all().filter(user=self.user_list[5]).update(confirmed=True,bumped=True)     

        cancelSession({},es.id)
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #test experiment
        e3 = createExperimentBlank()
        e3.institution.set(Institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.institutions_include.set(Institutions.objects.filter(Q(name="one") | Q(name="three")))

        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")
        
        # esd1 = es1.ESD.first()

        e_users = []
        # e_users.append(self.user_list[3])
        # e_users.append(self.user_list[4])

        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Users that done institution one and three:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #recuit subjects that have comitted for required insiution but not attended at recruit time and should not be included   
    def testOneInstitutionFutureComitted(self):
        """Test one institution required, subject is committed to future requirment""" 
        logger = logging.getLogger(__name__)

        #d_now_minus_one = self.d_now - timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        e=self.e2
        es=self.e2.ES.first()

        es.recruitment_params.institutions_include.set(Institutions.objects.filter(name="one"))
        es.recruitment_params.save()

        e_users = []

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Users that done institution one:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))
    
    #recruit subjects excluding one institution
    def testOneInstitutionExluded(self):
        """Test one institution excluded""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        esd1.ESDU_b.all().update(confirmed=False)
        #cancelAcceptInvitation({"id":es.id},self.user_list[1])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True, attended=False)
       
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        # esdu = esd1.ESDU_b.all().filter(user=self.user_list[1]).first()
        # logger.info("here:" + str(esdu.attended) + " " + str(esdu.confirmed))

        e=self.e2
        es=self.e2.ES.first()

        es.recruitment_params.institutions_exclude.set(Institutions.objects.filter(name="one"))
        es.recruitment_params.save()

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[2])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Users that have not done institution one:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #recruit subjects excluding two institutions if in all
    def testTwoInstitutionExcludedInAll(self):
        """Test two institutions excluded if in all""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)
        d_now_plus_one = self.d_now + timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        #setup experiment 1, insitution "one"
        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        esd1.ESDU_b.all().update(confirmed=False)
        # r = json.loads(cancelAcceptInvitation({"id":es.id},self.user_list[1]).content.decode("UTF-8"))
        # self.assertFalse(r['failed'])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)

        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #setup experiment 2 institution "one" and "three"
        e=self.e2
        es=self.e2.ES.first()
        esd1 = es.ESD.first()

        #esd1.ESDU_b.all().update(confirmed=False)
        #cancel all
        for i in e.ES.all():
            for j in i.ESD.all():
                for k in j.ESDU_b.all():
                    k.confirmed=False
                    k.save()

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[3]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[4]).update(confirmed=True,attended=True)  
        esd1.ESDU_b.all().filter(user=self.user_list[5]).update(confirmed=True,bumped=True)     
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #extra eperiment to give user one insitituion three experimence
        e4 = createExperimentBlank()
        e4.institution.set(Institutions.objects.filter(name="three"))
        e4.save()
       
        es1 = addSessionBlank(e4)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())

        esd1 = es1.ESD.first()
        
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_one.strftime("%Y-%m-%dT") + '11:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #add user one to experiment two, confirmed
        temp_u = self.user_list[1]
        es1.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},es1.id,False)

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)

        #test experiment
        e3 = createExperimentBlank()
        e3.institution.set(Institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.institutions_exclude.set(Institutions.objects.filter(Q(name="one") | Q(name="three")))

        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")
        
        # esd1 = es1.ESD.first()

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[2])
        e_users.append(self.user_list[5])
        e_users.append(self.user_list[6])
        e_users.append(self.user_list[7])


        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Users that done institution one and three:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

     #recruit subjects excluding two institutions if in all
    
    #recruit subjects excluding two institutions if in one
    def testTwoInstitutionExcludedInOne(self):
        """Test two institutions excluded if in one""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)
        d_now_plus_one = self.d_now + timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        #setup experiment 1, insitution "one"
        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        esd1.ESDU_b.all().update(confirmed=False)
        # r = json.loads(cancelAcceptInvitation({"id":es.id},self.user_list[1]).content.decode("UTF-8"))
        # self.assertFalse(r['failed'])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)

        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #setup experiment 2 institution "one" and "three"
        e=self.e2
        es=self.e2.ES.first()
        esd1 = es.ESD.first()

        #cancel all
        for i in e.ES.all():
            for j in i.ESD.all():
                for k in j.ESDU_b.all():
                    k.confirmed=False
                    k.save()

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[3]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[4]).update(confirmed=True,attended=True)  
        esd1.ESDU_b.all().filter(user=self.user_list[5]).update(confirmed=True,bumped=True)     
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #test experiment
        e3 = createExperimentBlank()
        e3.institution.set(Institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.institutions_exclude_all=False
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.institutions_exclude.set(Institutions.objects.filter(Q(name="one") | Q(name="three")))

        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")
        
        # esd1 = es1.ESD.first()

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[2])
        e_users.append(self.user_list[5])
        e_users.append(self.user_list[6])
        e_users.append(self.user_list[7])

        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Users that done institution one and three:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))   

    #recruit subjects excluding two institutions if in one future conflict
    def testInstitutionExcludedInOneFutureConflict(self):
        """Test two institutions excluded if in one, future conflict""" 
        logger = logging.getLogger(__name__)

        d_now_plus_two = self.d_now + timedelta(days=2)
        d_now_plus_one = self.d_now + timedelta(days=1)

        #unconfirm all
        ExperimentSessionDayUsers.objects.all().update(confirmed=False, attended=False, bumped=False)

        #setup experiment 1, insitution "one"
        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        # r = json.loads(cancelAcceptInvitation({"id":es.id},self.user_list[1]).content.decode("UTF-8"))
        # self.assertFalse(r['failed'])

        #move session 1 to future so experience is counted for future conflict
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_two.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True)
        # esd1.ESDU_b.all().filter(user=self.user_list[4]).update(confirmed=True)

        es.recruitment_params.institutions_exclude.set(Institutions.objects.filter(name="three"))

        #test experiment
        e3 = createExperimentBlank()
        e3.institution.set(Institutions.objects.filter(name="three"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.institutions_exclude_all=False
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.institutions_exclude.set(Institutions.objects.filter(Q(name="one")))
        es1.recruitment_params.save()

        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")
        
        # esd1 = es1.ESD.first()

        e_users = []
        e_users.append(self.user_list[0])
        #e_users.append(self.user_list[2])
        e_users.append(self.user_list[3])
        e_users.append(self.user_list[4])
        e_users.append(self.user_list[5])
        e_users.append(self.user_list[6])
        e_users.append(self.user_list[7])

        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Users that did institution one and three:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))   

    #check time overlap
    def testSessionOverlap(self):
        """Test that subjects can not commit two sessions at same time""" 
        logger = logging.getLogger(__name__)

        d_now_plus_two = self.d_now + timedelta(days=2)

        #logger.info("here:" + str(d_now_minus_one))

        #test experiment
        e3 = createExperimentBlank()
        e3.institution.set(Institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())

        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_two.strftime("%Y-%m-%dT") + '15:45','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[1])
        e_users.append(self.user_list[2])
        e_users.append(self.user_list[5])
        e_users.append(self.user_list[7])

        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Users that have time slot open:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

        #check ignore time
        esd1 = es1.ESD.first()
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_two.strftime("%Y-%m-%dT") + '15:45','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 0,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        e_users.append(self.user_list[3])
        e_users.append(self.user_list[4])
        e_users.append(self.user_list[6])

        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Users that have time slot open:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))
 
    #check time overlap with canceled session
    def testSessionOverlapCanceled(self):
        """Test that subjects can not commit two sessions at same time""" 
        logger = logging.getLogger(__name__)

        d_now_plus_two = self.d_now + timedelta(days=2)

        #logger.info("here:" + str(d_now_minus_one))

        cancelSession({},self.e2.ES.first().id)

        #test experiment
        e3 = createExperimentBlank()
        e3.institution.set(Institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())

        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_two.strftime("%Y-%m-%dT") + '15:45','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[1])
        e_users.append(self.user_list[2])
        e_users.append(self.user_list[3])
        e_users.append(self.user_list[4])
        e_users.append(self.user_list[5])
        e_users.append(self.user_list[7])

        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Users that done institution one:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #recruit subjects with one required experiment
    def testOneExperimentRequired(self):
        """Test one experiment required""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        esd1.ESDU_b.all().update(confirmed=False)
        # r = json.loads(cancelAcceptInvitation({"id":es.id},self.user_list[1]).content.decode("UTF-8"))
        # self.assertFalse(r['failed'])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)
       
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        # esdu = esd1.ESDU_b.all().filter(user=self.user_list[1]).first()
        # logger.info("here:" + str(esdu.attended) + " " + str(esdu.confirmed))

        e=self.e2
        es=self.e2.ES.first()

        es.recruitment_params.experiments_include.add(self.e1)
        es.recruitment_params.save()

        e_users = []
        e_users.append(self.user_list[1])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #recruit subjects with multiple experiment requirments, must be in all
    def testTwoExperimentsRequiredAll(self):
        """Test two experiments required, must be in all""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)
        d_now_plus_one = self.d_now + timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        #setup experiment 1, insitution "one"
        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        esd1.ESDU_b.all().update(confirmed=False)
        # r = json.loads(cancelAcceptInvitation({"id":es.id},self.user_list[1]).content.decode("UTF-8"))
        # self.assertFalse(r['failed'])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)

        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #setup experiment 2 institution "one" and "three"
        e=self.e2
        es=self.e2.ES.first()
        esd1 = es.ESD.first()

        #cancel all
        for i in e.ES.all():
            for j in i.ESD.all():
                for k in j.ESDU_b.all():
                    k.confirmed=False
                    k.save()

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))  
        self.assertEqual(r['status'],"success")

        #add user two to experiment two, confirmed
        temp_u = self.user_list[2]
        es.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},es.id,False)

        #add user two to experiment two, unconfirmed
        temp_u = self.user_list[1]
        es.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},es.id,False)

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)
        esd1.ESDU_b.all().filter(user=self.user_list[3]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[4]).update(confirmed=True,attended=True)  
        esd1.ESDU_b.all().filter(user=self.user_list[5]).update(confirmed=True,bumped=True)

        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #test experiment
        e3 = createExperimentBlank()
        e3.institution.set(Institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.experiments_include.add(self.e1)
        es1.recruitment_params.experiments_include.add(self.e2)

        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")
        
        # esd1 = es1.ESD.first()

        e_users = []
        e_users.append(self.user_list[1])

        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #recruit subjects with multiple experiment requirments, must be in one plus
    def testTwoExperimentsRequiredOnePlus(self):
        """Test two experiments required, must be in one or more""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)
        d_now_plus_one = self.d_now + timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        #setup experiment 1, insitution "one"
        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        esd1.ESDU_b.all().update(confirmed=False)
        # r = json.loads(cancelAcceptInvitation({"id":es.id},self.user_list[1]).content.decode("UTF-8"))
        # self.assertFalse(r['failed'])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)

        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #setup experiment 2 institution "one" and "three"
        e=self.e2
        es=self.e2.ES.first()
        esd1 = es.ESD.first()

        #cancel all
        for i in e.ES.all():
            for j in i.ESD.all():
                for k in j.ESDU_b.all():
                    k.confirmed=False
                    k.save()

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))  
        self.assertEqual(r['status'],"success")

        #add user two to experiment two, confirmed
        temp_u = self.user_list[2]
        es.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},es.id,False)

        #add user two to experiment two, unconfirmed
        temp_u = self.user_list[1]
        es.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},es.id,False)

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)
        esd1.ESDU_b.all().filter(user=self.user_list[3]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[4]).update(confirmed=True,attended=True)  
        esd1.ESDU_b.all().filter(user=self.user_list[5]).update(confirmed=True,bumped=True)

        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #test experiment
        e3 = createExperimentBlank()
        e3.institution.set(Institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.experiments_include.add(self.e1)
        es1.recruitment_params.experiments_include.add(self.e2)
        es1.recruitment_params.experiments_include_all=False
        es1.recruitment_params.save()

        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")
        
        # esd1 = es1.ESD.first()

        e_users = []
        e_users.append(self.user_list[1])
        e_users.append(self.user_list[3])
        e_users.append(self.user_list[4])

        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #recruit subjects with multiple experiment requirments, must be in one plus, canceled experiment
    def testTwoExperimentsRequiredOnePlusCanceled(self):
        """Test two experiments required, must be in one or more with canceled experiment""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)
        d_now_plus_one = self.d_now + timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        #setup experiment 1, insitution "one"
        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        esd1.ESDU_b.all().update(confirmed=False)
        # r = json.loads(cancelAcceptInvitation({"id":es.id},self.user_list[1]).content.decode("UTF-8"))
        # self.assertFalse(r['failed'])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)

        cancelSession({},es.id)
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #setup experiment 2 institution "one" and "three"
        e=self.e2
        es=self.e2.ES.first()
        esd1 = es.ESD.first()

        #cancel all
        for i in e.ES.all():
            for j in i.ESD.all():
                for k in j.ESDU_b.all():
                    k.confirmed=False
                    k.save()

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))  
        self.assertEqual(r['status'],"success")

        #add user two to experiment two, confirmed
        temp_u = self.user_list[2]
        es.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},es.id,False)

        #add user two to experiment two, unconfirmed
        temp_u = self.user_list[1]
        es.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},es.id,False)

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)
        esd1.ESDU_b.all().filter(user=self.user_list[3]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[4]).update(confirmed=True,attended=True)  
        esd1.ESDU_b.all().filter(user=self.user_list[5]).update(confirmed=True,bumped=True)

        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #test experiment
        e3 = createExperimentBlank()
        e3.institution.set(Institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.experiments_include.add(self.e1)
        es1.recruitment_params.experiments_include.add(self.e2)
        es1.recruitment_params.experiments_include_all=False
        es1.recruitment_params.save()

        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")
        
        # esd1 = es1.ESD.first()

        e_users = []
        e_users.append(self.user_list[1])
        e_users.append(self.user_list[3])
        e_users.append(self.user_list[4])

        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #recuit subjects that have comitted for required experiment but not attended at recruit time   
    def testOneExperimentFutureComitted(self):
        """Test one experiment required, subject comitted in future""" 
        logger = logging.getLogger(__name__)

        #d_now_minus_one = self.d_now - timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        e=self.e2
        es=self.e2.ES.first()

        es.recruitment_params.experiments_include.add(self.e1)
        es.recruitment_params.save()

        e_users = []

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #recruit subjects excluding one institution
    def testOneExperimentExluded(self):
        """Test one experiment excluded""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        esd1.ESDU_b.all().update(confirmed=False)
        #r = json.loads(cancelAcceptInvitation({"id":es.id},self.user_list[1]).content.decode("UTF-8"))

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)
       
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        e=self.e2
        es=self.e2.ES.first()

        es.recruitment_params.experiments_exclude.add(self.e1)
        es.recruitment_params.save()

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[2])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #recruit subjects excluding two experiments if in all
    def testTwoExperimentExcludedInAll(self):
        """Test two experiments excluded if in all""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)
        d_now_plus_one = self.d_now + timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        #setup experiment 1, insitution "one"
        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        esd1.ESDU_b.all().update(confirmed=False)
        # r = json.loads(cancelAcceptInvitation({"id":es.id},self.user_list[1]).content.decode("UTF-8"))
        # self.assertFalse(r['failed'])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_one.strftime("%Y-%m-%dT") + '11:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)

        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #setup experiment 2 institution "one" and "three"
        e=self.e2
        es=self.e2.ES.first()
        esd1 = es.ESD.first()

        #cancel all
        for i in e.ES.all():
            for j in i.ESD.all():
                for k in j.ESDU_b.all():
                    k.confirmed=False
                    k.save()

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #add user two to experiment two, unconfirmed
        temp_u = self.user_list[2]
        es.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},es.id,False)

        #add user one to experiment two, confirmed
        temp_u = self.user_list[1]
        es.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},es.id,False)

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)
        esd1.ESDU_b.all().filter(user=self.user_list[3]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[4]).update(confirmed=True,attended=True)  
        esd1.ESDU_b.all().filter(user=self.user_list[5]).update(confirmed=True,bumped=True)     
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #test experiment
        e3 = createExperimentBlank()
        e3.institution.set(Institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.experiments_exclude.set([self.e1,self.e2])

        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")
        
        # esd1 = es1.ESD.first()

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[2])
        e_users.append(self.user_list[3])
        e_users.append(self.user_list[4])
        e_users.append(self.user_list[5])
        e_users.append(self.user_list[6])
        e_users.append(self.user_list[7])


        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))
   
    #recruit subjects excluding two experiments if in one
    def testTwoExperimentExcludedInOne(self):
        """Test two experiments excluded if in One""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)
        d_now_plus_one = self.d_now + timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        #setup experiment 1, insitution "one"
        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        #cancel all
        for i in e.ES.all():
            for j in i.ESD.all():
                for k in j.ESDU_b.all():
                    k.confirmed=False
                    k.save()

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_one.strftime("%Y-%m-%dT") + '11:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True)

        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #setup experiment 2 institution "one" and "three"
        e=self.e2
        #cancel all
        for i in e.ES.all():
            for j in i.ESD.all():
                for k in j.ESDU_b.all():
                    k.confirmed=False
                    k.save()

        es=self.e2.ES.first()
        esd1 = es.ESD.first()

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_minus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #add user two to experiment two, unconfirmed
        temp_u = self.user_list[2]
        es.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},es.id,False)

        #add user one to experiment two, confirmed
        temp_u = self.user_list[1]
        es.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},es.id,False)

        esd1.ESDU_b.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)
        esd1.ESDU_b.all().filter(user=self.user_list[3]).update(confirmed=True,attended=True)
        esd1.ESDU_b.all().filter(user=self.user_list[4]).update(confirmed=True,attended=True)  
        esd1.ESDU_b.all().filter(user=self.user_list[5]).update(confirmed=True,bumped=True)     
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #test experiment
        e3 = createExperimentBlank()
        e3.institution.set(Institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.experiments_exclude.set([self.e1,self.e2])
        es1.recruitment_params.experiments_exclude_all=False
        es1.recruitment_params.save()

        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(self.l1.id),'date': d_now_plus_one.strftime("%Y-%m-%dT") + '14:00','length': '60','account': str(self.account1.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")
        
        # esd1 = es1.ESD.first()

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[5])
        e_users.append(self.user_list[6])
        e_users.append(self.user_list[7])

        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #test if changing gender parameters prevents confirmation
    def testGenderChangeConfirm(self):
        """Test changing gender requirments then confirming""" 
        logger = logging.getLogger(__name__)

        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()
        
        temp_u = self.user_list[1]
        temp_esdu = esd1.ESDU_b.get(user__id = temp_u.id)
        r = json.loads(changeConfirmationStatus({"userId":temp_u.id,"confirmed":"unconfirm","actionAll":"false","esduId":temp_esdu.id},es.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        r = json.loads(changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},es.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #remove all genders
        es.recruitment_params.gender.clear()
        es.save()
        esd1 = es.ESD.first()
        temp_esdu = esd1.ESDU_b.get(user__id = temp_u.id)

        #only check on recruiment email, not on confirmation
        r = json.loads(changeConfirmationStatus({"userId":temp_u.id,"confirmed":"unconfirm","actionAll":"false","esduId":temp_esdu.id},es.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        r = json.loads(changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},es.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"fail")

        self.assertEqual(es.recruitment_params.gender.count(),0)
    
    def testAllowList(self):
        """Allowed list""" 
        logger = logging.getLogger(__name__)

        e=self.e1
        es=self.e1.ES.first()
        
        #check only allowed users on list
        es.recruitment_params.allowed_list = []
        es.recruitment_params.allowed_list.append(self.user_list[0].id)

        es.recruitment_params.save()

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        self.assertIn(self.user_list[0], u_list)
        self.assertEqual(1, len(u_list))

        #check all users allowed
        es.recruitment_params.allowed_list = []
        es.recruitment_params.save()

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)
        self.assertEqual(6, len(u_list))
        
#test trait constrints
class traitConstraintTestCase(TestCase):
    e=None #experiment
    user_list=[]      #list of user
    staff_u=None
    t1 = None
    t2 = None

    def setUp(self):
        logger = logging.getLogger(__name__)

        p = parameters()
        p.save()
        
        d = Departments(name="d",charge_account="ca",petty_cash="0")
        d.save()

        a = Accounts(name="a",number="1.0",department=d)
        a.save()

        l=Locations(name="l",address="room")
        l.save()

        i1=Institutions(name="one")
        i1.save()
        i2=Institutions(name="two")
        i2.save()
        i3=Institutions(name="three")
        i3.save()

        s=schools.objects.first()
        s.email_filter.set(EmailFilters.objects.all())

        #staff user
        user_name = "s1@chapman.edu"
        temp_st =  subject_types.objects.get(id=3)
        self.staff_u = profileCreateUser(user_name,user_name,"zxcvb1234asdf","first","last","123456",\
                          Genders.objects.first(),"7145551234",Majors.objects.first(),\
                          temp_st,False,True,AccountTypes.objects.get(id=1))
        self.staff_u.is_staff=True
        self.staff_u.save()
        
        p.labManager=self.staff_u
        p.save()

        self.user_list=[]
        #create 5 subjects, 3 undergrad two graduates
        for g in range(4):

            if g<=2:
                user_name = "g"+str(g)+"@chapman.edu"
            else:
                user_name = "g"+str(g)+"@gmail.com"

            temp_st=""
            if g<=2:
                temp_st =  subject_types.objects.get(id=1)
                temp_at = AccountTypes.objects.get(id=2)
            else:
                temp_st =  subject_types.objects.get(id=2)
                temp_at = AccountTypes.objects.get(id=1)

            u = profileCreateUser(user_name,user_name,"zxcvb1234asdf","first","last","123456",\
                          Genders.objects.first(),"7145551234",Majors.objects.first(),\
                          temp_st,False,True,temp_at)
            
            logger.info(u)

            u.is_active = True
            u.profile.email_confirmed = 'yes'

            u.profile.save()
            u.save()

            u.profile.setup_email_filter()

            self.user_list.append(u)
        
        self.e = createExperimentBlank()
        self.e.institution.set(Institutions.objects.filter(name="one"))
        self.e.save()

        self.d_now = datetime.now(pytz.utc)
        d_now_plus_one = self.d_now + timedelta(days=1)
        d_now_plus_two = self.d_now + timedelta(days=2)

        self.t1 = Traits()
        self.t1.name="trait 1"
        self.t1.save()

        self.t2 = Traits()
        self.t2.name="trait 2"
        self.t2.save()

        pt = profile_trait()
        pt.trait = self.t1
        pt.value = 5
        pt.my_profile = self.user_list[1].profile
        pt.save()

        pt = profile_trait()
        pt.trait = self.t2
        pt.value = 7
        pt.my_profile = self.user_list[1].profile
        pt.save()

        pt = profile_trait()
        pt.trait = self.t1
        pt.value = 1
        pt.my_profile = self.user_list[2].profile
        pt.save()

        es1 = addSessionBlank(self.e)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(Genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.registration_cutoff = 5
        es1.recruitment_params.save()
        es1.save()
        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': {'location': str(l.id),'date': d_now_plus_one.strftime("%Y-%m-%dT") + '16:00','length': '60','account': str(a.id),'auto_reminder': 1,'enable_time': 1,'custom_reminder_time': 0,'reminder_time': '01/05/2021 12:04 pm -0800'}, 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")
    
    #no trait constraints
    def testNoConstraints(self):
        logger = logging.getLogger(__name__)

        es = self.e.ES.first()
        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[1])
        e_users.append(self.user_list[2])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        for u in u_list:
            self.assertIn(u, e_users)
        
        self.assertEqual(len(e_users), len(u_list))

    #One trait constraints
    def testOneConstraints(self):
        logger = logging.getLogger(__name__)

        es = self.e.ES.first()
        
        es.recruitment_params.trait_constraints_require_all = False
        es.recruitment_params.save()

        tc = Recruitment_parameters_trait_constraint()
        tc.max_value = 10
        tc.min_value = 5
        tc.trait = self.t1
        tc.recruitment_parameter = es.recruitment_params
        tc.save()

        #check 1 and 2 valid
        e_users = []
        
        e_users.append(self.user_list[1])
        #e_users.append(self.user_list[2])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        for u in u_list:
            self.assertIn(u, e_users)
        
        self.assertEqual(len(e_users), len(u_list))

        #check 1 only valid
        tc.min_value = 5
        tc.save()

        e_users = []
        
        e_users.append(self.user_list[1])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        for u in u_list:
            self.assertIn(u, e_users)
        
        self.assertEqual(len(e_users), len(u_list))

    #no trait constraints
    def testTwoConstraints(self):
        logger = logging.getLogger(__name__)

        es = self.e.ES.first()
        
        es.recruitment_params.trait_constraints_require_all = False
        es.recruitment_params.save()

        tc = Recruitment_parameters_trait_constraint()
        tc.max_value = 10
        tc.min_value = 0
        tc.trait = self.t1
        tc.recruitment_parameter = es.recruitment_params
        tc.save()

        tc2 = Recruitment_parameters_trait_constraint()
        tc2.max_value = 10
        tc2.min_value = 0
        tc2.trait = self.t2
        tc2.recruitment_parameter = es.recruitment_params
        tc2.save()

        #check 1 and 2 valid
        e_users = []
        
        e_users.append(self.user_list[1])
        e_users.append(self.user_list[2])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        for u in u_list:
            self.assertIn(u, e_users)
        
        self.assertEqual(len(e_users), len(u_list))

        #require both constraints
        es.recruitment_params.trait_constraints_require_all = True
        es.recruitment_params.save()

        e_users = []
        
        e_users.append(self.user_list[1])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        for u in u_list:
            self.assertIn(u, e_users)
        
        self.assertEqual(len(e_users), len(u_list))

        #check that one of two traits passes
        es.recruitment_params.trait_constraints_require_all = False
        es.recruitment_params.save()

        tc = es.recruitment_params.trait_constraints.first()
        tc.min_value = 9
        tc.save()

        e_users = []
        
        e_users.append(self.user_list[1])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        for u in u_list:
            self.assertIn(u, e_users)
        
        self.assertEqual(len(e_users), len(u_list))
    
    def test_one_exclude(self):
        logger = logging.getLogger(__name__)

        es = self.e.ES.first()
        
        es.recruitment_params.trait_constraints_require_all = False
        es.recruitment_params.save()

        tc = Recruitment_parameters_trait_constraint()
        tc.max_value = 3
        tc.min_value = 0
        tc.include_if_in_range = False
        tc.trait = self.t1
        tc.recruitment_parameter = es.recruitment_params
        tc.save()

        e_users = []
        
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[1])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        for u in u_list:
            self.assertIn(u, e_users)
        
        self.assertEqual(len(e_users), len(u_list))
    
    def test_two_exclude(self):
        logger = logging.getLogger(__name__)

        es = self.e.ES.first()
        
        es.recruitment_params.trait_constraints_require_all = False
        es.recruitment_params.save()

        tc = Recruitment_parameters_trait_constraint()
        tc.max_value = 3
        tc.min_value = 0
        tc.include_if_in_range = False
        tc.trait = self.t1
        tc.recruitment_parameter = es.recruitment_params
        tc.save()

        tc = Recruitment_parameters_trait_constraint()
        tc.max_value = 7
        tc.min_value = 7
        tc.include_if_in_range = False
        tc.trait = self.t2
        tc.recruitment_parameter = es.recruitment_params
        tc.save()

        e_users = []
        
        e_users.append(self.user_list[0])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        for u in u_list:
            self.assertIn(u, e_users)
        
        self.assertEqual(len(e_users), len(u_list))
    
    def test_one_exclude_one_include(self):
        logger = logging.getLogger(__name__)

        es = self.e.ES.first()
        
        es.recruitment_params.trait_constraints_require_all = False
        es.recruitment_params.save()

        tc = Recruitment_parameters_trait_constraint()
        tc.max_value = 3
        tc.min_value = 0
        tc.include_if_in_range = False
        tc.trait = self.t1
        tc.recruitment_parameter = es.recruitment_params
        tc.save()

        tc = Recruitment_parameters_trait_constraint()
        tc.max_value = 7
        tc.min_value = 7
        tc.include_if_in_range = True
        tc.trait = self.t2
        tc.recruitment_parameter = es.recruitment_params
        tc.save()

        e_users = []
        
        e_users.append(self.user_list[1])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        for u in u_list:
            self.assertIn(u, e_users)
        
        self.assertEqual(len(e_users), len(u_list))

#test school constraints
class schoolTestCase(TestCase):
    e=None #experiment
    user_list=[]      #list of user
    staff_u=None

    def setUp(self):
        logger = logging.getLogger(__name__)

        p = parameters()
        p.save()
        
        d = Departments(name="d",charge_account="ca",petty_cash="0")
        d.save()

        a = Accounts(name="a",number="1.0",department=d)
        a.save()

        l=Locations(name="l",address="room")
        l.save()

        i1=Institutions(name="one")
        i1.save()
        i2=Institutions(name="two")
        i2.save()
        i3=Institutions(name="three")
        i3.save()

        s=schools.objects.first()
        s.email_filter.set(EmailFilters.objects.all())

        self.user_list=[]
        #create 5 subjects, 3 undergrad two graduates
        for g in range(4):

            if g<=1:
                user_name = "g"+str(g)+"@chapman.edu"
            else:
                user_name = "g"+str(g)+"@gmail.com"

            temp_st=""
            if g<=2:
                temp_st =  subject_types.objects.get(id=1)
            else:
                temp_st =  subject_types.objects.get(id=2)

            u = profileCreateUser(user_name,user_name,"zxcvb1234asdf","first","last","123456",\
                          Genders.objects.first(),"7145551234",Majors.objects.first(),\
                          temp_st,False,True,AccountTypes.objects.get(id=2))
            
            logger.info(u)

            u.is_active = True
            u.profile.email_confirmed = 'yes'

            u.profile.save()
            u.save()

            u.profile.setup_email_filter()

            self.user_list.append(u)
        
        self.e = createExperimentBlank()
        self.e.institution.set(Institutions.objects.filter(name="one"))
        self.e.save()

        #staff user
        user_name = "s1@chapman.edu"
        temp_st =  subject_types.objects.get(id=3)
        self.staff_u = profileCreateUser(user_name,user_name,"zxcvb1234asdf","first","last","123456",\
                          Genders.objects.first(),"7145551234",Majors.objects.first(),\
                          temp_st,False,True,AccountTypes.objects.get(id=1))
        self.staff_u.is_staff=True
        self.staff_u.save()
        
        p.labManager=self.staff_u
        p.save()

    #no school contraints
    def testSchoolsNoContraint(self):
        """Test no school contraints""" 
        logger = logging.getLogger(__name__)

        es = addSessionBlank(self.e)    
        es.recruitment_params.reset_settings()
        es.recruitment_params.gender.set(Genders.objects.all())
        es.recruitment_params.subject_type.set(subject_types.objects.all())

        es.recruitment_params.schools_include_constraint=False
        es.recruitment_params.schools_exclude_constraint=False
        es.recruitment_params.save()

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[1])
        e_users.append(self.user_list[2])
        e_users.append(self.user_list[3])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        #all users should be valid without school contraints
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))
    
    #exclude school
    def testSchoolsExclude(self):
        """Test school exclude contraints""" 
        logger = logging.getLogger(__name__)

        es = addSessionBlank(self.e)    
        es.recruitment_params.reset_settings()
        es.recruitment_params.gender.set(Genders.objects.all())
        es.recruitment_params.subject_type.set(subject_types.objects.all())

        es.recruitment_params.schools_include_constraint=False
        es.recruitment_params.schools_exclude_constraint=True
        es.recruitment_params.schools_exclude.set(schools.objects.filter(id=1))
        es.recruitment_params.save()

        e_users = []
        #e_users.append(self.user_list[0])
        #e_users.append(self.user_list[1])
        e_users.append(self.user_list[2])
        e_users.append(self.user_list[3])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        #all users should be valid without school contraints
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))
    
    #include only from selected schools
    def testSchoolsInclude(self):
        """Test school include contraints""" 
        logger = logging.getLogger(__name__)

        es = addSessionBlank(self.e)    
        es.recruitment_params.reset_settings()
        es.recruitment_params.gender.set(Genders.objects.all())
        es.recruitment_params.subject_type.set(subject_types.objects.all())

        es.recruitment_params.schools_include_constraint=True
        es.recruitment_params.schools_exclude_constraint=False
        es.recruitment_params.schools_include.set(schools.objects.filter(id=1))
        es.recruitment_params.save()

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[1])
        #e_users.append(self.user_list[2])
        #e_users.append(self.user_list[3])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False,10)

        logger.info("Expected Users:")
        logger.info(e_users)
        logger.info("Returned Users:")
        logger.info(u_list)

        #all users should be valid without school contraints
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))