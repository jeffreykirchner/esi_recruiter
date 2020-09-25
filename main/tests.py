from django.test import TestCase

from django.contrib.auth.models import User
from main.views.profileCreate import profileCreateUser
from main.models import genders,experiments,subject_types,account_types,majors,\
                        parameters,accounts,departments,locations,institutions,schools,email_filters,\
                        experiment_session_day_users    
from main.views.staff.experimentSearchView import createExperimentBlank
from main.views.staff.experimentView import addSessionBlank
from main.views.staff.experimentSessionView import changeConfirmationStatus,updateSessionDay,cancelSession
from main.views.subject.subjectHome import acceptInvitation,cancelAcceptInvitation
from main.views.staff.experimentSessionRunView import attendSubject,bumpSubject,noShowSubject,completeSession

from datetime import datetime,timedelta
import pytz
import logging
from django.db.models import Q,F


# Create your tests here.
#test gender
class GenderTestCase(TestCase):
    def setUp(self):
        logger = logging.getLogger(__name__)

        p = parameters()
        p.save()
        
        d = departments(name="d",charge_account="ca",petty_cash="0")
        d.save()

        a = accounts(name="a",number="1.0",department=d)
        a.save()

        l=locations(name="l",address="room")
        l.save()

        i1=institutions(name="one")
        i1.save()
        i2=institutions(name="two")
        i2.save()
        i3=institutions(name="three")
        i3.save()

        s=schools.objects.get(id=1)
        s.email_filter.set(email_filters.objects.all())

        #create 4 gendered users
        for g in genders.objects.all():
            user_name = "g"+str(g.id)+"@chapman.edu"

            u = profileCreateUser(user_name,user_name,"zxcvb1234asdf","first","last","123456",\
                          genders.objects.get(id=g.id),"7145551234",majors.objects.first(),\
                          subject_types.objects.get(id=1),False,True,account_types.objects.get(id=2))
            
            logger.info(u)

            u.is_active = True
            u.profile.email_confirmed = 'yes'

            u.profile.save()
            u.save()

            u.profile.setup_email_filter()
        
        e = createExperimentBlank()
        e.institution.set(institutions.objects.filter(name="one"))
        e.save()
    
    def testWomenOnly(self):
        """Test only females are recruited""" 
        logger = logging.getLogger(__name__)
        
        e=experiments.objects.first()

        #women only test
        es_women_only = addSessionBlank(e)    
        es_women_only.recruitment_params.reset_settings()
        es_women_only.recruitment_params.gender.set(genders.objects.filter(name="Female"))
        es_women_only.recruitment_params.subject_type.set(subject_types.objects.filter(id=1))
       
        u_list = es_women_only.getValidUserList_forward_check([],True,0,0,[],False)
        c=len(u_list)

        self.assertEqual(c, len(genders.objects.filter(name="Female")))

    def testAll(self):
        """Test all genders are recruited""" 

        e=experiments.objects.first()

        es_all = addSessionBlank(e)    
        es_all.recruitment_params.reset_settings()
        es_all.recruitment_params.gender.set(genders.objects.all())
        es_all.recruitment_params.subject_type.set(subject_types.objects.filter(id=1))

        u_list = es_all.getValidUserList_forward_check([],True,0,0,[],False)
        c=len(u_list)
               
        self.assertEqual(c, len(genders.objects.all()))

#test subject types
class subjectTypeTestCase(TestCase):
    def setUp(self):
        logger = logging.getLogger(__name__)

        p = parameters()
        p.save()
        
        d = departments(name="d",charge_account="ca",petty_cash="0")
        d.save()

        a = accounts(name="a",number="1.0",department=d)
        a.save()

        l=locations(name="l",address="room")
        l.save()

        i1=institutions(name="one")
        i1.save()
        i2=institutions(name="two")
        i2.save()
        i3=institutions(name="three")
        i3.save()

        s=schools.objects.first()
        s.email_filter.set(email_filters.objects.all())

        #create 5 subjects, 3 undergrad two graduates
        for g in range(5):
            user_name = "g"+str(g)+"@chapman.edu"

            temp_st=""
            if g<=2:
                temp_st =  subject_types.objects.get(id=1)
            else:
                temp_st =  subject_types.objects.get(id=2)

            u = profileCreateUser(user_name,user_name,"zxcvb1234asdf","first","last","123456",\
                          genders.objects.first(),"7145551234",majors.objects.first(),\
                          temp_st,False,True,account_types.objects.get(id=2))
            
            logger.info(u)

            u.is_active = True
            u.profile.email_confirmed = 'yes'

            u.profile.save()
            u.save()

            u.profile.setup_email_filter()
        
        e = createExperimentBlank()
        e.institution.set(institutions.objects.filter(name="one"))
        e.save()
    
    #undergrad only
    def testSubjectTypeUndergraduate(self):
        """Test subject type undergraduate""" 
        logger = logging.getLogger(__name__)
        
        e=experiments.objects.first()

        es = addSessionBlank(e)    
        es.recruitment_params.reset_settings()
        es.recruitment_params.gender.set(genders.objects.all())
        es.recruitment_params.subject_type.set(subject_types.objects.filter(id=1))
       
        u_list = es.getValidUserList_forward_check([],True,0,0,[],False)
        c=len(u_list)

        self.assertEqual(c, len(User.objects.filter(profile__subject_type=subject_types.objects.get(id=1)))) 

    #get all types
    def testSubjectTypeAll(self):
        """Test subject type all""" 
        logger = logging.getLogger(__name__)
        
        e=experiments.objects.first() 

        es = addSessionBlank(e)    
        es.recruitment_params.reset_settings()
        es.recruitment_params.gender.set(genders.objects.all())
        es.recruitment_params.subject_type.set(subject_types.objects.all())
       
        u_list = es.getValidUserList_forward_check([],True,0,0,[],False)
        c=len(u_list)

        self.assertEqual(c, len(User.objects.all()))

#test experience count
class recruiteTestCase(TestCase):
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
        logger = logging.getLogger(__name__)

        self.p = parameters()
        self.p.save()
        
        d = departments(name="d",charge_account="ca",petty_cash="0")
        d.save()

        self.account1 = accounts(name="a",number="1.0",department=d)
        self.account1.save()

        self.l1=locations(name="room1",address="room1")
        self.l1.save()
        self.l2=locations(name="room2",address="room2")
        self.l2.save()

        i1=institutions(name="one")
        i1.save()
        i2=institutions(name="two")
        i2.save()
        i3=institutions(name="three")
        i3.save()

        s=schools.objects.first()
        s.email_filter.set(email_filters.objects.all())

        #staff user
        user_name = "s1@chapman.edu"
        temp_st =  subject_types.objects.get(id=3)
        self.staff_u = profileCreateUser(user_name,user_name,"zxcvb1234asdf","first","last","123456",\
                          genders.objects.first(),"7145551234",majors.objects.first(),\
                          temp_st,False,True,account_types.objects.get(id=1))
        self.staff_u.is_superuser=True
        self.staff_u.save()
        
        self.p.labManager=self.staff_u
        self.p.save()

        self.user_list=[]

        #create 7 subjects
        for g in range(8):
            user_name = "g"+str(g)+"@chapman.edu"
            temp_st =  subject_types.objects.get(id=1)

            u = profileCreateUser(user_name,user_name,"zxcvb1234asdf","first","last","123456",\
                          genders.objects.first(),"7145551234",majors.objects.first(),\
                          temp_st,False,True,account_types.objects.get(id=2))
            
            logger.info(u)

            u.is_active = True
            u.profile.email_confirmed = 'yes'

            u.profile.save()
            u.save()

            u.profile.setup_email_filter()

            self.user_list.append(u)
        
        logger.info(self.user_list)

        self.d_now = datetime.now(pytz.utc)
        d_now_plus_one = self.d_now + timedelta(days=1)
        d_now_plus_two = self.d_now + timedelta(days=2)
        
        #setup experiment with one session two subjects, one confirmed, +1 day
        self.e1 = createExperimentBlank()
        self.e1.institution.set(institutions.objects.filter(name="one"))
        self.e1.save()

        es1 = addSessionBlank(self.e1)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_one.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        temp_u = self.user_list[1]
        es1.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.experiment_session_day_users_set.filter(user__id = temp_u.id).first()
        changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","esduId":temp_esdu.id},es1.id)

        temp_u = self.user_list[2]
        es1.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.experiment_session_day_users_set.filter(user__id = temp_u.id).first()
        changeConfirmationStatus({"userId":temp_u.id,"confirmed":"unconfirm","esduId":temp_esdu.id},es1.id)

        #setup experiment with one session three subjects, one confirmed, +2 day
        self.e2 = createExperimentBlank()
        self.e2.institution.set(institutions.objects.filter(Q(name="one") | Q(name="three")))
        self.e2.save()

        es1 = addSessionBlank(self.e2)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': str(esd1.id), 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_two.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        temp_u = self.user_list[3]
        es1.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.experiment_session_day_users_set.filter(user__id = temp_u.id).first()
        changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","esduId":temp_esdu.id},es1.id)

        temp_u = self.user_list[4]
        es1.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.experiment_session_day_users_set.filter(user__id = temp_u.id).first()
        changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","esduId":temp_esdu.id},es1.id)

        temp_u = self.user_list[5]
        es1.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.experiment_session_day_users_set.filter(user__id = temp_u.id).first()
        changeConfirmationStatus({"userId":temp_u.id,"confirmed":"unconfirm","esduId":temp_esdu.id},es1.id)     

        # #add overlapping session in another room
        es1 = addSessionBlank(self.e2)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l2.id)}, {'name': 'date', 'value': d_now_plus_two.strftime("%#m/%#d/%Y") + ' 04:30 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}   
        updateSessionDay(session_day_data,esd1.id)

        temp_u = self.user_list[6]
        es1.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.experiment_session_day_users_set.filter(user__id = temp_u.id).first()
        changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","esduId":temp_esdu.id},es1.id)

        #3rd session later 1 player
        es1 = addSessionBlank(self.e2)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_two.strftime("%#m/%#d/%Y") + ' 06:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}   
        updateSessionDay(session_day_data,esd1.id)

        temp_u = self.user_list[7]
        es1.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.experiment_session_day_users_set.filter(user__id = temp_u.id).first()
        changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","esduId":temp_esdu.id},es1.id)
    
    #subject g0 is unassinged

    #constraint disabled
    def testExperienceCountOff(self):
        """Test experience count off""" 
        logger = logging.getLogger(__name__)

        e=self.e2
        es=self.e2.ES.first()

        es.recruitment_params.experience_constraint=False
        es.recruitment_params.save()

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False)

        e_users = experiment_session_day_users.objects.filter(experiment_session_day__experiment_session__experiment__id = e.id,
                                                              confirmed=True)\
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

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False)

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[2])

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

        #esd1.experiment_session_day_users_set.all().update(confirmed=False)
        cancelAcceptInvitation({"id":es.id},self.user_list[1])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_minus_one.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)
        completeSession({},esd1.id)

        e=self.e2
        es=self.e2.ES.first()

        #esdu = esd1.experiment_session_day_users_set.all().filter(user__username="g1@chapman.edu").first()

        #logger.info("here:" + str(esdu.attended))

        es.recruitment_params.experience_constraint=True
        es.recruitment_params.experience_min = 1
        es.recruitment_params.experience_max = 1000
        es.recruitment_params.save()

        e_users = []
        e_users.append(self.user_list[1])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False)

        logger.info("Users not confirmed for experiment with 1 experience:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #one or more experiments
    def testExperienceCountOnePlusCanceled(self):
        """Test experience count 1+ experience canceled experiment""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        #esd1.experiment_session_day_users_set.all().update(confirmed=False)
        cancelAcceptInvitation({"id":es.id},self.user_list[1])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_minus_one.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)

        cancelSession({},es.id)
        completeSession({},esd1.id)

        e=self.e2
        es=self.e2.ES.first()

        #esdu = esd1.experiment_session_day_users_set.all().filter(user__username="g1@chapman.edu").first()

        #logger.info("here:" + str(esdu.attended))

        es.recruitment_params.experience_constraint=True
        es.recruitment_params.experience_min = 1
        es.recruitment_params.experience_max = 1000
        es.recruitment_params.save()

        e_users = []
       
        u_list = es.getValidUserList_forward_check([],True,0,0,[],False)

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

        #esd1.experiment_session_day_users_set.all().update(confirmed=False)
        cancelAcceptInvitation({"id":es.id},self.user_list[1])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_minus_one.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[1]).update(confirmed=True)
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)
        completeSession({},esd1.id)

        esdu = esd1.experiment_session_day_users_set.all().filter(user=self.user_list[1]).first()
        logger.info("here:" + str(esdu.attended) + " " + str(esdu.confirmed))

        e=self.e2
        es=self.e2.ES.first()

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[2])

        self.p.noShowCutoff = 1
        self.p.save()

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False)

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

        #esd1.experiment_session_day_users_set.all().update(confirmed=False)
        cancelAcceptInvitation({"id":es.id},self.user_list[1])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_minus_one.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[1]).update(confirmed=True)
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)
       
        cancelSession({},es.id)
        completeSession({},esd1.id)

        # esdu = esd1.experiment_session_day_users_set.all().filter(user=self.user_list[1]).first()
        # logger.info("here:" + str(esdu.attended) + " " + str(esdu.confirmed))

        e=self.e2
        es=self.e2.ES.first()

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[1])
        e_users.append(self.user_list[2])

        self.p.noShowCutoff = 1
        self.p.save()

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False)

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

        #esd1.experiment_session_day_users_set.all().update(confirmed=False)
        cancelAcceptInvitation({"id":es.id},self.user_list[1])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_minus_one.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)
       
        completeSession({},esd1.id)

        # esdu = esd1.experiment_session_day_users_set.all().filter(user=self.user_list[1]).first()
        # logger.info("here:" + str(esdu.attended) + " " + str(esdu.confirmed))

        e=self.e2
        es=self.e2.ES.first()

        es.recruitment_params.institutions_include.set(institutions.objects.filter(name="one"))
        es.recruitment_params.save()

        e_users = []
        e_users.append(self.user_list[1])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False)

        logger.info("Users that done institution one:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #recruit subjects with multiple institution requirments
    def testTwoInstitutionRequired(self):
        """Test two institutions required""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)
        d_now_plus_one = self.d_now + timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        #setup experiment 1, insitution "one"
        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        #esd1.experiment_session_day_users_set.all().update(confirmed=False)
        cancelAcceptInvitation({"id":es.id},self.user_list[1])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_minus_one.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)

        completeSession({},esd1.id)

        #setup experiment 2 institution "one" and "three"
        e=self.e2
        es=self.e2.ES.first()
        esd1 = es.ESD.first()

        #esd1.experiment_session_day_users_set.all().update(confirmed=False)
        cancelAcceptInvitation({"id":es.id},self.user_list[3])
        cancelAcceptInvitation({"id":es.id},self.user_list[4])
        cancelAcceptInvitation({"id":es.id},self.user_list[5])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_minus_one.strftime("%#m/%#d/%Y") + ' 02:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[3]).update(confirmed=True,attended=True)
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[4]).update(confirmed=True,attended=True)  
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[5]).update(confirmed=True,bumped=True)     
        completeSession({},esd1.id)

        #test experiment
        e3 = createExperimentBlank()
        e3.institution.set(institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.institutions_include.set(institutions.objects.filter(Q(name="one") | Q(name="three")))

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_one.strftime("%#m/%#d/%Y") + ' 02:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)
        
        # esd1 = es1.ESD.first()

        e_users = []
        e_users.append(self.user_list[3])
        e_users.append(self.user_list[4])

        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False)

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

        #esd1.experiment_session_day_users_set.all().update(confirmed=False)
        cancelAcceptInvitation({"id":es.id},self.user_list[1])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_minus_one.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)

        completeSession({},esd1.id)

        #setup experiment 2 institution "one" and "three"
        e=self.e2
        es=self.e2.ES.first()
        esd1 = es.ESD.first()

        #esd1.experiment_session_day_users_set.all().update(confirmed=False)
        cancelAcceptInvitation({"id":es.id},self.user_list[3])
        cancelAcceptInvitation({"id":es.id},self.user_list[4])
        cancelAcceptInvitation({"id":es.id},self.user_list[5])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_minus_one.strftime("%#m/%#d/%Y") + ' 02:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[3]).update(confirmed=True,attended=True)
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[4]).update(confirmed=True,attended=True)  
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[5]).update(confirmed=True,bumped=True)     

        cancelSession({},es.id)
        completeSession({},esd1.id)

        #test experiment
        e3 = createExperimentBlank()
        e3.institution.set(institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.institutions_include.set(institutions.objects.filter(Q(name="one") | Q(name="three")))

        esd1 = es.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_one.strftime("%#m/%#d/%Y") + ' 02:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)
        
        # esd1 = es1.ESD.first()

        e_users = []
        # e_users.append(self.user_list[3])
        # e_users.append(self.user_list[4])

        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False)

        logger.info("Users that done institution one and three:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))

    #recuit subjects that have comitted for required insiution but not attended at recruit time   
    def testOneInstitutionFutureComitted(self):
        """Test one institution required""" 
        logger = logging.getLogger(__name__)

        #d_now_minus_one = self.d_now - timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        e=self.e2
        es=self.e2.ES.first()

        es.recruitment_params.institutions_include.set(institutions.objects.filter(name="one"))
        es.recruitment_params.save()

        e_users = []

        u_list = es.getValidUserList_forward_check([],True,0,0,[],True)

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

        #esd1.experiment_session_day_users_set.all().update(confirmed=False)
        cancelAcceptInvitation({"id":es.id},self.user_list[1])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_minus_one.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)
       
        completeSession({},esd1.id)

        # esdu = esd1.experiment_session_day_users_set.all().filter(user=self.user_list[1]).first()
        # logger.info("here:" + str(esdu.attended) + " " + str(esdu.confirmed))

        e=self.e2
        es=self.e2.ES.first()

        es.recruitment_params.institutions_exclude.set(institutions.objects.filter(name="one"))
        es.recruitment_params.save()

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[2])

        u_list = es.getValidUserList_forward_check([],True,0,0,[],False)

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

        #esd1.experiment_session_day_users_set.all().update(confirmed=False)
        cancelAcceptInvitation({"id":es.id},self.user_list[1])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_minus_one.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)

        completeSession({},esd1.id)

        #setup experiment 2 institution "one" and "three"
        e=self.e2
        es=self.e2.ES.first()
        esd1 = es.ESD.first()

        #esd1.experiment_session_day_users_set.all().update(confirmed=False)
        cancelAcceptInvitation({"id":es.id},self.user_list[3])
        cancelAcceptInvitation({"id":es.id},self.user_list[4])
        cancelAcceptInvitation({"id":es.id},self.user_list[5])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_minus_one.strftime("%#m/%#d/%Y") + ' 02:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[3]).update(confirmed=True,attended=True)
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[4]).update(confirmed=True,attended=True)  
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[5]).update(confirmed=True,bumped=True)     
        completeSession({},esd1.id)

        #test experiment
        e3 = createExperimentBlank()
        e3.institution.set(institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.institutions_exclude.set(institutions.objects.filter(Q(name="one") | Q(name="three")))

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_one.strftime("%#m/%#d/%Y") + ' 02:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)
        
        # esd1 = es1.ESD.first()

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[1])
        e_users.append(self.user_list[2])
        e_users.append(self.user_list[5])
        e_users.append(self.user_list[6])
        e_users.append(self.user_list[7])


        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False)

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

        #esd1.experiment_session_day_users_set.all().update(confirmed=False)
        cancelAcceptInvitation({"id":es.id},self.user_list[1])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_minus_one.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)

        completeSession({},esd1.id)

        #setup experiment 2 institution "one" and "three"
        e=self.e2
        es=self.e2.ES.first()
        esd1 = es.ESD.first()

        #esd1.experiment_session_day_users_set.all().update(confirmed=False)
        cancelAcceptInvitation({"id":es.id},self.user_list[3])
        cancelAcceptInvitation({"id":es.id},self.user_list[4])
        cancelAcceptInvitation({"id":es.id},self.user_list[5])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_minus_one.strftime("%#m/%#d/%Y") + ' 02:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[3]).update(confirmed=True,attended=True)
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[4]).update(confirmed=True,attended=True)  
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[5]).update(confirmed=True,bumped=True)     
        completeSession({},esd1.id)

        #test experiment
        e3 = createExperimentBlank()
        e3.institution.set(institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(genders.objects.all())
        es1.recruitment_params.institutions_exclude_all=False
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.institutions_exclude.set(institutions.objects.filter(Q(name="one") | Q(name="three")))

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_one.strftime("%#m/%#d/%Y") + ' 02:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)
        
        # esd1 = es1.ESD.first()

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[2])
        e_users.append(self.user_list[5])
        e_users.append(self.user_list[6])
        e_users.append(self.user_list[7])

        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False)

        logger.info("Users that done institution one and three:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))   

    #recruit subjects excluding two institutions if in one future conflict
    def testTwoInstitutionExcludedInOneFutureConflict(self):
        """Test two institutions excluded if in one, future conflict""" 
        logger = logging.getLogger(__name__)

        d_now_minus_one = self.d_now - timedelta(days=1)
        d_now_plus_one = self.d_now + timedelta(days=1)

        #logger.info("here:" + str(d_now_minus_one))

        #setup experiment 1, insitution "one"
        e=self.e1
        es=self.e1.ES.first()
        esd1 = es.ESD.first()

        #esd1.experiment_session_day_users_set.all().update(confirmed=False)
        cancelAcceptInvitation({"id":es.id},self.user_list[1])

        #move session 1 experiment 1 into past so experience is counted
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_minus_one.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[1]).update(confirmed=True,attended=True)
        esd1.experiment_session_day_users_set.all().filter(user=self.user_list[2]).update(confirmed=True,bumped=True)

        completeSession({},esd1.id)

        #setup experiment 2 institution "one" and "three", exclude two experience
        e=self.e2
        es=self.e2.ES.first()
        esd1 = es.ESD.first()

        es.recruitment_params.institutions_exclude.set(institutions.objects.filter(name="two"))

        #test experiment
        e3 = createExperimentBlank()
        e3.institution.set(institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(genders.objects.all())
        es1.recruitment_params.institutions_exclude_all=False
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.institutions_exclude.set(institutions.objects.filter(Q(name="one") | Q(name="three")))

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_one.strftime("%#m/%#d/%Y") + ' 02:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)
        
        # esd1 = es1.ESD.first()

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[2])
        e_users.append(self.user_list[5])
        e_users.append(self.user_list[6])
        e_users.append(self.user_list[7])

        u_list = es1.getValidUserList_forward_check([],True,0,0,[],False)

        logger.info("Users that done institution one and three:")
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
        e3.institution.set(institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())

        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_two.strftime("%#m/%#d/%Y") + ' 03:45 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[1])
        e_users.append(self.user_list[2])
        e_users.append(self.user_list[5])
        e_users.append(self.user_list[7])

        u_list = es1.getValidUserList_forward_check([],True,0,0,[],True)

        logger.info("Users that done institution one:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
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
        e3.institution.set(institutions.objects.filter(name="two"))
        e3.save()
       
        es1 = addSessionBlank(e3)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())

        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_two.strftime("%#m/%#d/%Y") + ' 03:45 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': '1'}], 'sessionCanceledChangedMessage': False}
        updateSessionDay(session_day_data,esd1.id)

        e_users = []
        e_users.append(self.user_list[0])
        e_users.append(self.user_list[1])
        e_users.append(self.user_list[2])
        e_users.append(self.user_list[3])
        e_users.append(self.user_list[4])
        e_users.append(self.user_list[5])
        e_users.append(self.user_list[7])

        u_list = es1.getValidUserList_forward_check([],True,0,0,[],True)

        logger.info("Users that done institution one:")
        logger.info(e_users)
        logger.info("Valid users that can be added:")
        logger.info(u_list)

        #all users not in experiment that have been in at least one other session
        for u in e_users:
            self.assertIn(u, u_list)
        
        self.assertEqual(len(e_users),len(u_list))