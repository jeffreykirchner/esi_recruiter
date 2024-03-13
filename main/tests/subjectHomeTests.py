from datetime import datetime, timedelta

import json
import pytz
import logging
import sys

from django.contrib.sessions.middleware import SessionMiddleware

from django.test import TestCase
from django.test import RequestFactory
from django.test import Client

from main.models import genders
from main.models import subject_types
from main.models import account_types
from main.models import majors
from main.models import parameters
from main.models import accounts
from main.models import departments
from main.models import locations
from main.models import institutions
from main.models import schools
from main.models import email_filters
from main.models import ConsentForm         
from main.models import ProfileConsentForm           
from main.models import UmbrellaConsentForm
from main.models import experiment_session_day_users

from main.views import profileCreateUser
from main.views import update_profile
from main.views import createExperimentBlank
from main.views import addSessionBlank
from main.views import updateSessionDay
from main.views import acceptInvitation
from main.views import cancelAcceptInvitation

from main.views.staff.experiment_session_run_view import attendSubject, noShowSubject, bumpSubject

import main

class subjectHomeTestCase(TestCase):

    fixtures = ['subject_types.json', 'ConsentForm.json', 'UmbrellaConsentForm.json']

    e1 = None         #experiments
    e2 = None

    es1 = None        #sessions 
    es2 = None

    u = None            #user
    d_now = None       #date time now
    l1 = None           #locations
    l2 = None
    l1 = None           #locations
    l2 = None
    account1 = None     #accounts   
    p = None            #parameters
    staff_u = None      #staff user

    def setUp(self):
        sys._called_from_test = True

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
        self.staff_u.is_staff=True
        self.staff_u.save()
        
        self.p.labManager=self.staff_u
        self.p.save()

        self.u = profileCreateUser("u1@chapman.edu","u1@chapman.edu","zxcvb1234asdf","first","last","123456",\
                          genders.objects.first(),"7145551234",majors.objects.first(),\
                          subject_types.objects.get(id=1),False,True,account_types.objects.get(id=2))
        
        logger.info(self.u)

        self.u.is_active = True
        self.u.profile.email_confirmed = 'yes'

        self.u.profile.save()
        self.u.save()

        self.u.profile.setup_email_filter()
        
        self.d_now = datetime.now(pytz.utc)
        d_now_plus_two = self.d_now + timedelta(days=2)
        d_now_plus_three = self.d_now + timedelta(days=3)
        
        #setup experiment two days from now
        self.e1 = createExperimentBlank()
        self.e1.institution.set(institutions.objects.filter(name="one"))
        self.e1.consent_form_default = ConsentForm.objects.first()
        self.e1.save()

        self.es1 = addSessionBlank(self.e1)    
        self.es1.recruitment_params.reset_settings()
        self.es1.recruitment_params.gender.set(genders.objects.all())
        self.es1.recruitment_params.subject_type.set(subject_types.objects.all())
        self.es1.recruitment_params.registration_cutoff = 5
        self.es1.recruitment_params.save()
        self.es1.save()
        esd1 = self.es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_two.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'},{'name': 'custom_reminder_time', 'value': 'false'}, {'name': 'reminder_time', 'value': '01/05/2021 12:04 pm -0800'}], 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")


        self.es1.addUser(self.u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = self.u.id).first()
        #changeConfirmationStatus({"userId":self.u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},self.es1.id)

        #setup experiment three days from now
        self.e2 = createExperimentBlank()
        self.e2.institution.set(institutions.objects.filter(name="two"))
        self.e2.consent_form_default = ConsentForm.objects.first()
        self.e2.save()

        self.es2 = addSessionBlank(self.e2)    
        self.es2.recruitment_params.reset_settings()
        self.es2.recruitment_params.gender.set(genders.objects.all())
        self.es2.recruitment_params.subject_type.set(subject_types.objects.all())
        self.es2.recruitment_params.registration_cutoff = 5
        self.es2.recruitment_params.save()
        self.es2.save()
        esd1 = self.es2.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_three.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'},{'name': 'custom_reminder_time', 'value': 'false'}, {'name': 'reminder_time', 'value': '01/05/2021 12:04 pm -0800'}], 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")


        self.es2.addUser(self.u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = self.u.id).first()
        #changeConfirmationStatus({"userId":self.u.id,"confirmed":"unconfirm","actionAll":"false","esduId":temp_esdu.id},self.es2.id)

    #subject confirms attendence to an experiment where there are no conflicts
    def testConfirmAttendenceNoConflict(self):
        """Test subject confirm and cancel no conflicts""" 
        logger = logging.getLogger(__name__)

        #add consent form
        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])

        r = json.loads(acceptInvitation({"id":self.es2.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])

        r = json.loads(cancelAcceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])

        r = json.loads(cancelAcceptInvitation({"id":self.es2.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])
    
    #subject must have agreed to consent form before accepting
    def testConfirmAttendenceConsent_required(self):
        """Test subject consent required acceptence""" 
        logger = logging.getLogger(__name__)
   

        #no subject does not have required consent form
        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertTrue(r['failed'])
        self.assertEqual("Invitation failed no consent.", r['message'])

        #add consent form
        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])
        self.assertEqual("", r['message'])

        #remove confirmations
        experiment_session_day_users.objects.filter(user__id=self.u.id).update(attended=False,confirmed=False)

        #test no consent form required by session
        profile_consent_form.delete()

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertTrue(r['failed'])
        self.assertEqual("Invitation failed no consent.", r['message'])

        self.es1.consent_form=None
        self.es1.save()

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])
        self.assertEqual("", r['message'])

        #remove confirmations
        experiment_session_day_users.objects.filter(user__id=self.u.id).update(attended=False,confirmed=False)

        #test no agreement required
        self.es1.consent_form=ConsentForm.objects.first()
        self.es1.save()

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertTrue(r['failed'])
        self.assertEqual("Invitation failed no consent.", r['message'])

        self.es1.consent_form.agreement_required=False
        self.es1.consent_form.save()

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])
        self.assertEqual("", r['message'])


    #subject must have agreed to umbrella consent form before accepting
    def testConfirmAttendenceUmbreallaConsent_required(self):
        """Test subject umbrella consent required acceptence""" 
        logger = logging.getLogger(__name__)

        #add consent form
        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        #check confirm without umbrella consent
        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])
        self.assertEqual("", r['message'])

        #remove confirmations
        experiment_session_day_users.objects.filter(user__id=self.u.id).update(attended=False,confirmed=False)

        #enable umbrella consent
        umbrella_consent = UmbrellaConsentForm.objects.first()
        umbrella_consent.active=True
        umbrella_consent.save()

        # subject does not have required consent form
        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertTrue(r['failed'])
        self.assertEqual("Invitation failed no policy consent.", r['message'])

        #subject has required consent form
        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=umbrella_consent.consent_form)
        profile_consent_form.save()

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])
        self.assertEqual("", r['message'])

    #Subject must re-consent if bumped from past session
    def testReConsentIfBumped(self):
        """Subject must re-consent if bumped from past session""" 

        logger = logging.getLogger(__name__)

        # data = {'action': 'getCurrentInvitations'}
        # request = RequestFactory().post(f'/subjectHome/', data=data, content_type="application/json")
        # result = main.views.SubjectHome.post(request)

        c = Client()
        c.force_login(self.u)
        response = c.post('/subjectHome/', {'action': 'getCurrentInvitations'}, content_type="application/json", follow=True)
        r = json.loads(response.content.decode("UTF-8"))

        #check no consent
        self.assertFalse(r['upcomingInvitations'][0]['consented'])
        self.assertFalse(r['upcomingInvitations'][1]['consented'])

        #accept and conesent
        response = c.post(f'/subjectConsent/{self.es1.id}/session/sign/',
                          {'action': 'acceptConsentForm',
                           'consent_form_id' : self.es1.consent_form.id, 
                           'consent_form_signature' : [], 
                           'consent_form_signature_resolution' : {'width':0, 'height':0}}, 
                          content_type="application/json", 
                          follow=True)
        r = json.loads(response.content.decode("UTF-8"))
        self.assertFalse(r['failed'])        

        #check no consent after accept
        response = c.post('/subjectHome/', {'action': 'getCurrentInvitations'}, content_type="application/json", follow=True)
        r = json.loads(response.content.decode("UTF-8"))
        
        self.assertFalse(r['upcomingInvitations'][0]['consented'])
        self.assertFalse(r['upcomingInvitations'][1]['consented'])

        #attend subject check that consent now exists
        esd1 = self.es1.ESD.first()
        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id, user__id = self.u.id).first()
        r = json.loads(attendSubject({"id":esdu.id},esd1.id,self.staff_u,).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status'])

        response = c.post('/subjectHome/', {'action': 'getCurrentInvitations'}, content_type="application/json", follow=True)
        r = json.loads(response.content.decode("UTF-8"))
        
        self.assertTrue(r['upcomingInvitations'][0]['consented'])
        self.assertTrue(r['upcomingInvitations'][1]['consented'])

        #bump subject, check that consent no longer exists
        #attend subject check that consent now exists
        esd1 = self.es1.ESD.first()
        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id, user__id = self.u.id).first()
        r = json.loads(bumpSubject({"id":esdu.id},esd1.id,self.staff_u,).content.decode("UTF-8"))
        self.assertIn("success",r['status'])

        response = c.post('/subjectHome/', {'action': 'getCurrentInvitations'}, content_type="application/json", follow=True)
        r = json.loads(response.content.decode("UTF-8"))
        
        self.assertFalse(r['upcomingInvitations'][0]['consented'])
        self.assertFalse(r['upcomingInvitations'][1]['consented'])
    
    #subject cancels attendence within 24 hours
    def testCancelAttendenceWithin24Hours(self):
        """Test subject cancel within 24 hours""" 
        logger = logging.getLogger(__name__)

        esd1 = self.es1.ESD.first()

        d_now = self.d_now
    
        #add consent form
        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now.strftime("%#m/%#d/%Y") + ' 11:59 pm -0000'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'},{'name': 'custom_reminder_time', 'value': 'false'}, {'name': 'reminder_time', 'value': '01/05/2021 12:04 pm -0800'}], 'sessionCanceledChangedMessage': False}
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

        #add consent form
        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

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

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_two.strftime("%#m/%#d/%Y") + ' 01:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'},{'name': 'custom_reminder_time', 'value': 'false'}, {'name': 'reminder_time', 'value': '01/05/2021 12:04 pm -0800'}], 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #add consent form
        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()


        temp_es1.addUser(self.u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = self.u.id).first()

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])
        self.assertEqual("", r['message'])


        r = json.loads(acceptInvitation({"id":temp_es1.id},self.u).content.decode("UTF-8"))
        self.assertTrue(r['failed'])
        self.assertEqual("Invitation failed recruitment violation.", r['message'])

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

        temp_u.profile.save()
        temp_u.save()

        temp_u.profile.setup_email_filter()

        #add consent form
        profile_consent_form = ProfileConsentForm(my_profile=temp_u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        self.es1.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        #changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},self.es1.id)

        r = json.loads(acceptInvitation({"id":self.es1.id},temp_u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])
        self.assertEqual("", r['message'])

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertTrue(r['failed'])
        self.assertEqual("Invitation failed accept session full.", r['message'])

        #change limit to 2
        self.es1.recruitment_params.registration_cutoff = 2
        self.es1.recruitment_params.save()

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])
        self.assertEqual("", r['message'])
    
    #test accept when the session is full
    def testExperimentIsSurvey(self):
        """Test accept when the session is full""" 
        logger = logging.getLogger(__name__)

        self.es1.experiment.survey = True
        self.es1.experiment.save()

        esd1 = self.es1.ESD.first()

        temp_u = profileCreateUser("u2@chapman.edu","u2@chapman.edu","zxcvb1234asdf","first","last","123456",\
                          genders.objects.first(),"7145551234",majors.objects.first(),\
                          subject_types.objects.get(id=1),False,True,account_types.objects.get(id=2))
        
        logger.info(temp_u)

        temp_u.is_active = True
        temp_u.profile.email_confirmed = 'yes'

        temp_u.profile.save()
        temp_u.save()

        temp_u.profile.setup_email_filter()

        #add consent form
        profile_consent_form = ProfileConsentForm(my_profile=temp_u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        self.es1.addUser(temp_u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = temp_u.id).first()
        #changeConfirmationStatus({"userId":temp_u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},self.es1.id)

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertTrue(r['failed'])
        self.assertEqual("Invitation failed experiment is survey.", r['message'])

        #set survey to fase
        self.es1.experiment.survey = False
        self.es1.experiment.save()

        r = json.loads(acceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])
        self.assertEqual("", r['message'])

    def test_update_profile(self):
        '''
        test updating profile
        '''

        self.u.profile.email_confirmed="yes"
        self.u.profile.save()

        request = {}
        request['user'] = self.u

        profile_data={'action': 'update', 'formData': [{'name': 'first_name', 'value': 'Sam'}, {'name': 'last_name', 'value': 'I Am'}, {'name': 'chapman_id', 'value': '123456789'}, {'name': 'email', 'value': 'abc@123.edu'}, {'name': 'phone', 'value': '1231239999'}, {'name': 'gender', 'value': '1'}, {'name': 'major', 'value': '1'}, {'name': 'subject_type', 'value': '2'}, {'name': 'studentWorker', 'value': 'Yes'}, {'name': 'paused', 'value': 'Yes'}, {'name': 'password1', 'value': ''}, {'name': 'password2', 'value': ''}]}
        r = json.loads(update_profile(self.u, profile_data).content.decode("UTF-8"))
        self.assertEqual(r['status'], "success")

        self.assertEqual(self.u.first_name,"Sam")
        self.assertEqual(self.u.last_name,"I am")
        self.assertEqual(self.u.profile.studentID,"123456789")
        self.assertEqual(self.u.email,"abc@123.edu")
        self.assertEqual(self.u.profile.phone,"1231239999")
        self.assertEqual(self.u.profile.gender.id, 1)
        self.assertEqual(self.u.profile.major.id, 1)
        self.assertEqual(self.u.profile.subject_type.id, 2)
        self.assertEqual(self.u.profile.studentWorker, True)
        self.assertEqual(self.u.profile.paused, True)
        self.assertNotEqual(self.u.profile.email_confirmed, 'yes')
        
