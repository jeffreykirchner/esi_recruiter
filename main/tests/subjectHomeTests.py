from django.test import TestCase
import unittest

from django.contrib.auth.models import User

from main.views.profileCreate import profileCreateUser
from main.models import genders,experiments,subject_types,account_types,majors,\
                        parameters,accounts,departments,locations,institutions,schools,email_filters,\
                        experiment_session_day_users    
from main.views.staff.experimentSearchView import createExperimentBlank
from main.views.staff.experimentView import addSessionBlank
from main.views.staff.experimentSessionView import changeConfirmationStatus,updateSessionDay,cancelSession
from main.views.subject.subjectHome import acceptInvitation,cancelAcceptInvitation

from datetime import datetime,timedelta
import pytz
import logging
from django.db.models import Q,F
import json
import ast

class subjectHomeTestCase(TestCase):

    e1 = None         #experiments
    e2 = None

    es1 = None        #sessions 
    es2 = None

    u=None            #user
    d_now = None      #date time now
    l1=None           #locations
    l2=None
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

        self.u = profileCreateUser("u1@chapman.edu","u1@chapman.edu","zxcvb1234asdf","first","last","123456",\
                          genders.objects.first(),"7145551234",majors.objects.first(),\
                          subject_types.objects.get(id=1),False,True,account_types.objects.get(id=2))
        
        logger.info(self.u)

        self.u.is_active = True
        self.u.profile.email_confirmed = 'yes'
        self.u.profile.consentRequired = False

        self.u.profile.save()
        self.u.save()

        self.u.profile.setup_email_filter()
        
        self.d_now = datetime.now(pytz.utc)
        d_now_plus_two = self.d_now + timedelta(days=2)
        d_now_plus_three = self.d_now + timedelta(days=3)
        
        #setup experiment two days from now
        self.e1 = createExperimentBlank()
        self.e1.institution.set(institutions.objects.filter(name="one"))
        self.e1.save()

        self.es1 = addSessionBlank(self.e1)    
        self.es1.recruitment_params.reset_settings()
        self.es1.recruitment_params.gender.set(genders.objects.all())
        self.es1.recruitment_params.subject_type.set(subject_types.objects.all())
        self.es1.recruitment_params.registration_cutoff = 5
        self.es1.recruitment_params.save()
        self.es1.save()
        esd1 = self.es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_two.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'}], 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")


        self.es1.addUser(self.u.id,self.staff_u,True)
        temp_esdu = esd1.experiment_session_day_users_set.filter(user__id = self.u.id).first()
        #changeConfirmationStatus({"userId":self.u.id,"confirmed":"confirm","esduId":temp_esdu.id},self.es1.id)

        #setup experiment three days from now
        self.e2 = createExperimentBlank()
        self.e2.institution.set(institutions.objects.filter(name="two"))
        self.e2.save()

        self.es2 = addSessionBlank(self.e2)    
        self.es2.recruitment_params.reset_settings()
        self.es2.recruitment_params.gender.set(genders.objects.all())
        self.es2.recruitment_params.subject_type.set(subject_types.objects.all())
        self.es2.recruitment_params.registration_cutoff = 5
        self.es2.recruitment_params.save()
        self.es2.save()
        esd1 = self.es2.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_three.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'}], 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")


        self.es2.addUser(self.u.id,self.staff_u,True)
        temp_esdu = esd1.experiment_session_day_users_set.filter(user__id = self.u.id).first()
        #changeConfirmationStatus({"userId":self.u.id,"confirmed":"unconfirm","esduId":temp_esdu.id},self.es2.id)

    #subject confirms attendence to an experiment where there are no conflicts
    def testConfirmAttendenceNoConflict(self):
        """Test subject confirm and cancel no conflicts""" 
        logger = logging.getLogger(__name__)

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])

        r = json.loads(acceptInvitation({"id":self.es2.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])

        r = json.loads(cancelAcceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])

        r = json.loads(cancelAcceptInvitation({"id":self.es2.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])
    
    #subject must have agreed to consent form before accepting
    def testConfirmAttendenceConsentRequired(self):
        """Test subject consent required acceptence""" 
        logger = logging.getLogger(__name__)

        self.u.profile.consentRequired = True
        self.u.profile.save()

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertTrue(r['failed'])

        self.u.profile.consentRequired = False
        self.u.profile.save()

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])

    #subject cancels attendence within 24 hours
    def testCancelAttendenceWithin24Hours(self):
        """Test subject cancel within 24 hours""" 
        logger = logging.getLogger(__name__)

        esd1 = self.es1.ESD.first()

        d_now = self.d_now

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now.strftime("%#m/%#d/%Y") + ' 11:59 pm -0000'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'}], 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")


        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])

        r = json.loads(cancelAcceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertTrue(r['failed'])

    #subject cancels attendence within 24 hours
    def testAttendCancelSpoofData(self):
        """Test subject with junk / fake data""" 
        logger = logging.getLogger(__name__)

        r = json.loads(acceptInvitation({},self.u).content.decode("UTF-8"))
        self.assertTrue(r['failed'])

    #subject confirm future institution conflict
    def testConfirmWithFutureIstitutionConflict(self):
        """Test subject confirm with future institution conflict""" 
        logger = logging.getLogger(__name__)

        self.es2.recruitment_params.institutions_exclude.set(institutions.objects.filter(name="one"))
        self.es2.recruitment_params.save()

        #try to accept experiment 2 after being in experiment 1
        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])

        r = json.loads(acceptInvitation({"id":self.es2.id},self.u).content.decode("UTF-8"))
        self.assertTrue(r['failed'])

        r = json.loads(cancelAcceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])

        #try to accept experiment 1 after 2
        r = json.loads(acceptInvitation({"id":self.es2.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertTrue(r['failed'])

        r = json.loads(cancelAcceptInvitation({"id":self.es2.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])
    
    #subject confirms form same experiment twice
    def testConfirmSameExperimentTwice(self):
        """Test subject confirm in same experiment twice""" 
        logger = logging.getLogger(__name__)

        temp_es1 = addSessionBlank(self.e1)    
        temp_es1.recruitment_params.reset_settings()
        temp_es1.recruitment_params.gender.set(genders.objects.all())
        temp_es1.recruitment_params.subject_type.set(subject_types.objects.all())
        temp_es1.recruitment_params.registration_cutoff = 5
        temp_es1.recruitment_params.save()
        temp_es1.save()
        esd1 = temp_es1.ESD.first()

        d_now_plus_two = self.d_now + timedelta(days=2)

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_two.strftime("%#m/%#d/%Y") + ' 01:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'}], 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")


        temp_es1.addUser(self.u.id,self.staff_u,True)
        temp_esdu = esd1.experiment_session_day_users_set.filter(user__id = self.u.id).first()

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])

        r = json.loads(acceptInvitation({"id":temp_es1.id},self.u).content.decode("UTF-8"))
        self.assertTrue(r['failed'])

    #test accept when the session is full
    def testSessionNotFull(self):
        """Test accept when the session is full""" 
        logger = logging.getLogger(__name__)

        self.es1.recruitment_params.registration_cutoff = 1
        self.es1.recruitment_params.save()

        esd1 = self.es1.ESD.first()

        temp_u = profileCreateUser("u2@chapman.edu","u2@chapman.edu","zxcvb1234asdf","first","last","123456",\
                          genders.objects.first(),"7145551234",majors.objects.first(),\
                          subject_types.objects.get(id=1),False,True,account_types.objects.get(id=2))
        
        logger.info(temp_u)

        temp_u.is_active = True
        temp_u.profile.email_confirmed = 'yes'
        temp_u.profile.consentRequired = False

        temp_u.profile.save()
        temp_u.save()

        temp_u.profile.setup_email_filter()

        self.es1.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.experiment_session_day_users_set.filter(user__id = temp_u.id).first()
        #changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","esduId":temp_esdu.id},self.es1.id)

        r = json.loads(acceptInvitation({"id":self.es1.id},temp_u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertTrue(r['failed'])

        #change limit to 2
        self.es1.recruitment_params.registration_cutoff = 2
        self.es1.recruitment_params.save()

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])



