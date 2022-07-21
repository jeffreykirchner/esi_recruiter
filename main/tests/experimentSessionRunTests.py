from datetime import datetime, timedelta
import pytz
import logging
import json
import io

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import TestCase

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
from main.models import experiment_session_day_users
from main.models import ProfileConsentForm
from main.models import ConsentForm

from main.views.registration import profileCreateUser
from main.views.staff.experiment_search_view import createExperimentBlank
from main.views.staff.experiment_view import addSessionBlank
from main.views.staff.experiment_session_view import changeConfirmationStatus, updateSessionDay, cancelSession, removeSubject
from main.views.staff.experiment_session_run_view import getStripeReaderCheckin, noShowSubject, attendSubject, bumpSubject, noShowSubject,fillDefaultShowUpFee
from main.views.staff.experiment_session_run_view import fillEarningsWithFixed, completeSession, savePayouts, backgroundSave, bumpAll, autoBump, completeSession, takeEarningsUpload
from main.views.subject.subject_home import cancelAcceptInvitation, acceptInvitation

class sessionRunTestCase(TestCase):
    fixtures = ['subject_types.json', 'ConsentForm.json']

    e1 = None         #experiments
    e2 = None

    es1 = None        #sessions 
    es2 = None

    u=None            #user
    u2=None
    u3=None

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
        self.staff_u = profileCreateUser(user_name, user_name, "zxcvb1234asdf", "first", "last", "123456",\
                          genders.objects.first(),"7145551234",majors.objects.first(),\
                          temp_st, False, True, account_types.objects.get(id=1))
        self.staff_u.is_staff = True
        self.staff_u.is_staff = True
        self.staff_u.save()
        
        self.p.labManager=self.staff_u
        self.p.save()

        #subject 1
        self.u = profileCreateUser("u1@chapman.edu","u1@chapman.edu","zxcvb1234asdf","first","last","00123456",\
                          genders.objects.first(),"7145551234",majors.objects.first(),\
                          subject_types.objects.get(id=1),False,True,account_types.objects.get(id=2))
        
        logger.info(self.u)

        self.u.is_active = True
        self.u.profile.email_confirmed = 'yes'

        self.u.profile.save()
        self.u.save()

        self.u.profile.setup_email_filter()

        #subject 2
        self.u2 = profileCreateUser("u2@chapman.edu","u2@chapman.edu","zxcvb1234asdf","first","last","001234",\
                    genders.objects.first(),"7145551234",majors.objects.first(),\
                    subject_types.objects.get(id=1),False,True,account_types.objects.get(id=2))
        
        logger.info(self.u2)

        self.u2.is_active = True
        self.u2.profile.email_confirmed = 'yes'

        self.u2.profile.save()
        self.u2.save()

        self.u2.profile.setup_email_filter()

        #subject 3
        self.u3 = profileCreateUser("u3@chapman.edu","u3@chapman.edu","zxcvb1234asdf","first","last","00121212",\
                    genders.objects.first(),"7145551234",majors.objects.first(),\
                    subject_types.objects.get(id=1),False,True,account_types.objects.get(id=2))
        
        logger.info(self.u2)

        self.u3.is_active = True
        self.u3.profile.email_confirmed = 'yes'

        self.u3.profile.save()
        self.u3.save()

        self.u3.profile.setup_email_filter()
        
        #sessions
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

        #add subject 1
        self.es1.addUser(self.u.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = self.u.id).first()
        r = json.loads(changeConfirmationStatus({"userId":self.u.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},self.es1.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")


        #add subject 2
        self.es1.addUser(self.u2.id,self.staff_u,True)
        temp_esdu = esd1.ESDU_b.filter(user__id = self.u2.id).first()
        r = json.loads(changeConfirmationStatus({"userId":self.u2.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},self.es1.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

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
        esd2 = self.es2.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd2.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_three.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'},{'name': 'custom_reminder_time', 'value': 'false'}, {'name': 'reminder_time', 'value': '01/05/2021 12:04 pm -0800'}], 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd2.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #add subject 1
        self.es2.addUser(self.u.id,self.staff_u,True)
        temp_esdu = esd2.ESDU_b.filter(user__id = self.u.id).first()
        r = json.loads(changeConfirmationStatus({"userId":self.u.id,"confirmed":"unconfirm","actionAll":"false","esduId":temp_esdu.id},self.es2.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")


        #add subject 2
        self.es2.addUser(self.u2.id,self.staff_u,True)
        temp_esdu = esd2.ESDU_b.filter(user__id = self.u2.id).first()
        r = json.loads(changeConfirmationStatus({"userId":self.u2.id,"confirmed":"confirm","actionAll":"false","esduId":temp_esdu.id},self.es1.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")


    #check subject in with stripe reader
    def testStripeReaderCheckin(self):
        """Test subject confirm and cancel no conflicts""" 
        logger = logging.getLogger(__name__)

        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        profile_consent_form = ProfileConsentForm(my_profile=self.u2.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        profile_consent_form = ProfileConsentForm(my_profile=self.u3.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        esd1 = self.es1.ESD.first()

        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()
        self.assertIsInstance(esdu,experiment_session_day_users)

        #check leading zeros
        r = json.loads(getStripeReaderCheckin({"value":";00123456=1234",
                                                   "autoAddUsers":False,
                                                   "ignoreConstraints":False},
                                               esd1.id,
                                               self.staff_u).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status']['message'])

        r = json.loads(noShowSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        #check no zeros
        r = json.loads(getStripeReaderCheckin({"value":";123456=1234",
                                                   "autoAddUsers":False,
                                                   "ignoreConstraints":False},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status']['message'])

        r = json.loads(noShowSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        #check no equals
        r = json.loads(getStripeReaderCheckin({"value":";123456",
                                                   "autoAddUsers":False,
                                                   "ignoreConstraints":False},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertNotIn("is now attending",r['status']['message'])

        r = json.loads(noShowSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        #check no semi colon
        r = json.loads(getStripeReaderCheckin({"value":"123456=",
                                                   "autoAddUsers":False,
                                                   "ignoreConstraints":False},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertNotIn("is now attending",r['status']['message'])

        r = json.loads(noShowSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        #check wrong number
        r = json.loads(getStripeReaderCheckin({"value":";56456565=",
                                                   "autoAddUsers":False,
                                                   "ignoreConstraints":False},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertNotIn("is now attending",r['status']['message'])

        r = json.loads(noShowSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        #check checkin similar id numbers
        r = json.loads(getStripeReaderCheckin({"value":";1234=",
                                                   "autoAddUsers":False,
                                                   "ignoreConstraints":False},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertNotIn("is now attending",r['status']['message'])

        r = json.loads(noShowSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        #check in unconfirmed
        r = json.loads(changeConfirmationStatus({"userId":self.u.id,"confirmed":"unconfirm","actionAll":"false","esduId":esdu.id},self.es1.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        r = json.loads(getStripeReaderCheckin({"value":";00123456=1234",
                                                   "autoAddUsers":False,
                                                   "ignoreConstraints":False},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertNotIn("is now attending",r['status']['message'])

        r = json.loads(noShowSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertNotIn("is now attending",r['status'])

        #check add to session
        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id, user__id = self.u3.id).first()
        self.assertEquals(esdu,None)

        r = json.loads(getStripeReaderCheckin({"value":";00121212=1234",
                                                   "autoAddUsers":True,
                                                   "ignoreConstraints":False},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status']['message'])

        #check add again:
        r = json.loads(getStripeReaderCheckin({"value":";00121212=1234",
                                                   "autoAddUsers":True,
                                                   "ignoreConstraints":False},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status']['message'])

        #check recruitment violation
        #remove user 3 from sessoin
        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u3.id).first()

        r = json.loads(noShowSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        r = json.loads(changeConfirmationStatus({"userId":self.u3.id,"confirmed":"unconfirm","actionAll":"false","esduId":esdu.id},self.es1.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        r = json.loads(removeSubject({"userId":self.u3.id,
                                      "esduId":"",},self.es1.id).content.decode("UTF-8"))
        self.assertIn("success",r['status'])

        #remove all genders
        self.es1.recruitment_params.gender.clear()
        self.es1.recruitment_params.save()

        r = json.loads(getStripeReaderCheckin({"value":";00121212=1234",
                                                   "autoAddUsers":True,
                                                   "ignoreConstraints":False},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertNotIn("is now attending",r['status']['message'])

        r = json.loads(getStripeReaderCheckin({"value":";00121212=1234",
                                                   "autoAddUsers":True,
                                                   "ignoreConstraints":True},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status']['message'])

    #allow super user to manually check subject in
    def testAttendSubject(self):
        """Test super user manual check in""" 
        logger = logging.getLogger(__name__)

        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        profile_consent_form = ProfileConsentForm(my_profile=self.u2.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        profile_consent_form = ProfileConsentForm(my_profile=self.u3.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        esd1 = self.es1.ESD.first()
        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()

        #super user check in
        r = json.loads(attendSubject({"id":esdu.id},esd1.id,self.staff_u,).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status'])

        r = json.loads(noShowSubject({"id":esdu.id},esd1.id,self.staff_u,).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        #unconfirmed user checkin
        esdu.confirmed=False
        esdu.save()
        r = json.loads(attendSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertNotIn("is now attending",r['status'])

        r = json.loads(noShowSubject({"id":esdu.id},esd1.id,self.staff_u,).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        #none super user user manaul check in 
        self.staff_u.is_staff=False
        self.staff_u.save()

        r = json.loads(attendSubject({"id":esdu.id},esd1.id,self.staff_u,).content.decode("UTF-8"))
        self.assertNotIn("is now attending",r['status'])

        r = json.loads(noShowSubject({"id":esdu.id},esd1.id,self.staff_u,).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        #attend subject not exists
        r = json.loads(attendSubject({"id":esdu.id+50},esd1.id,self.staff_u,).content.decode("UTF-8"))
        self.assertNotIn("is now attending",r['status'])

        r = json.loads(noShowSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])
    
    #test bumping subjects
    def testBumpSubject(self):
        """Test bump subjects""" 
        logger = logging.getLogger(__name__)

        esd1 = self.es1.ESD.first()
        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()

        #bump subject
        r = json.loads(bumpSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertIn("success",r['status'])

        r = json.loads(noShowSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        #bump subject not exists
        r = json.loads(bumpSubject({"id":esdu.id+50},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertNotIn("success",r['status'])

        r = json.loads(noShowSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        #bump subject not confirmed
        esdu.confirmed=False
        esdu.save()
        r = json.loads(bumpSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertNotIn("success",r['status'])

        r = json.loads(noShowSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

    #test no showing subjects
    def testNoShowSubject(self):
        """Test no show subjects""" 
        logger = logging.getLogger(__name__)

        esd1 = self.es1.ESD.first()
        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()

        r = json.loads(noShowSubject({"id":esdu.id+50},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertNotEquals("success",r['status'])

    #test fill with fixed earnings amount
    def testFillEarningsWithFixedAmount(self):
        """Test fill earning with fixed amount""" 
        logger = logging.getLogger(__name__)

        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        profile_consent_form = ProfileConsentForm(my_profile=self.u2.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        profile_consent_form = ProfileConsentForm(my_profile=self.u3.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        esd1 = self.es1.ESD.first()
        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()
        esdu2 = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u2.id).first()

        #one confirmed, one no show
        r = json.loads(attendSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status'])

        r = json.loads(noShowSubject({"id":esdu2.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        r = json.loads(fillEarningsWithFixed({"amount":6.23},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()
        esdu2 = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u2.id).first()

        self.assertEquals(float(esdu.earnings),6.23)
        self.assertEquals(float(esdu2.earnings),0)

        #bumped
        r = json.loads(bumpSubject({"id":esdu2.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        r = json.loads(fillEarningsWithFixed({"amount":6.23},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        esdu2 = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u2.id).first()
        self.assertEquals(float(esdu2.earnings),0)

        #session not found
        r = json.loads(fillEarningsWithFixed({},esd1.id+50,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("fail",r['status'])
    
    #test fill with default show up fees
    def testFillDefaultShowUpFee(self):
        """Test fill default show up fees""" 
        logger = logging.getLogger(__name__)

        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        profile_consent_form = ProfileConsentForm(my_profile=self.u2.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        esd1 = self.es1.ESD.first()
        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()
        esdu2 = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u2.id).first()

        #one confirmed, one no show
        r = json.loads(attendSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status'])

        r = json.loads(noShowSubject({"id":esdu2.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        r = json.loads(fillDefaultShowUpFee({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()
        esdu2 = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u2.id).first()

        self.assertEquals(esdu.show_up_fee,esd1.experiment_session.experiment.showUpFee)
        self.assertEquals(esdu2.show_up_fee,0)

        #bumped
        r = json.loads(bumpSubject({"id":esdu2.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        r = json.loads(fillDefaultShowUpFee({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        esdu2 = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u2.id).first()
        self.assertEquals(esdu2.show_up_fee,esd1.experiment_session.experiment.showUpFee)

        #session not found
        r = json.loads(fillDefaultShowUpFee({},esd1.id+50,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("fail",r['status'])

    #test complete session button
    def testCompleteSession(self):
        """Test complete session""" 
        logger = logging.getLogger(__name__)

        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        profile_consent_form = ProfileConsentForm(my_profile=self.u2.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        esd1 = self.es1.ESD.first()
        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()
        esdu2 = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u2.id).first()

        #fill with earnings then bump, check earnings removed
        r = json.loads(attendSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status'])

        r = json.loads(attendSubject({"id":esdu2.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status'])

        r = json.loads(fillEarningsWithFixed({"amount":6.23},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        r = json.loads(bumpSubject({"id":esdu2.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()
        esdu2 = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u2.id).first()

        self.assertEquals(float(esdu.earnings),6.23)
        self.assertEquals(float(esdu2.earnings),0)

        #check now show earnings bump fee
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        r = json.loads(attendSubject({"id":esdu2.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status'])

        r = json.loads(fillEarningsWithFixed({"amount":6.23},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        r = json.loads(fillDefaultShowUpFee({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        r = json.loads(noShowSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()
        esdu2 = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u2.id).first()

        self.assertEquals(float(esdu.earnings),0)
        self.assertEquals(float(esdu.earnings),0)

        #test invalid session day
        r = json.loads(completeSession({},esd1.id+50,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("fail",r['status'])

    #test reopening session
    def testReopenSession(self):
        logger = logging.getLogger(__name__)

        #create empty session
        es1 = addSessionBlank(self.e1)    
        es1.recruitment_params.reset_settings()
        es1.recruitment_params.gender.set(genders.objects.all())
        es1.recruitment_params.subject_type.set(subject_types.objects.all())
        es1.recruitment_params.registration_cutoff = 5
        es1.recruitment_params.save()
        es1.save()

        esd1 = es1.ESD.first()

        self.d_now = datetime.now(pytz.utc)
        d_now_minus_two = self.d_now - timedelta(days=2)

        esd1 = es1.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_minus_two.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'},{'name': 'custom_reminder_time', 'value': 'false'}, {'name': 'reminder_time', 'value': '01/05/2021 12:04 pm -0800'}], 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        self.staff_u.is_staff=False
        self.staff_u.save()

        #check no super user reopen past session
        #close session
        esd1 = es1.ESD.first()
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        #reopen
        esd1 = es1.ESD.first()
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("fail",r['status'])

        self.staff_u.is_staff=True
        self.staff_u.save()

        esd1 = es1.ESD.first()
        r = json.loads(completeSession({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

    #test save payouts
    def testSavePayouts(self):
        """Test save payouts""" 
        logger = logging.getLogger(__name__)
        
        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        esd1 = self.es1.ESD.first()
        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()

        #save attend subject's pay out
        r = json.loads(attendSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status'])

        p = {"payoutList" : [{"id":esdu.id,"earnings":6.23,"showUpFee":7.00}]}

        r = json.loads(savePayouts(p,esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()

        self.assertEquals(float(esdu.earnings),6.23)
        self.assertEquals(float(esdu.show_up_fee),7.00)

        #try to save junk
        p = {"payoutList" : [{"id":esdu.id,"earnings":"a","showUpFee":"b"}]}

        r = json.loads(savePayouts(p,esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("fail",r['status'])

        #save to user that does not exist
        p = {"payoutList" : [{"id":esdu.id + 50,"earnings":6.23,"showUpFee":7.00}]}

        r = json.loads(savePayouts(p,esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("fail",r['status'])

        #save junk
        p = {"payoutList" : [{"id":esdu.id + 50,"showUpFee":7.00}]}

        r = json.loads(savePayouts(p,esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("fail",r['status'])
    
    #test background save
    def testBackgroundSave(self):
        """Test background save payouts""" 
        logger = logging.getLogger(__name__)

        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        profile_consent_form = ProfileConsentForm(my_profile=self.u2.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        profile_consent_form = ProfileConsentForm(my_profile=self.u3.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        esd1 = self.es1.ESD.first()
        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()

        #save attend subject's pay out
        r = json.loads(attendSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status'])

        p = {"payoutList" : [{"id":esdu.id,"earnings":6.23,"showUpFee":7.00}]}

        r = json.loads(backgroundSave(p,esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()

        self.assertEquals(float(esdu.earnings),6.23)
        self.assertEquals(float(esdu.show_up_fee),7.00)

        #try to save junk
        p = {"payoutList" : [{"id":esdu.id,"earnings":"a","showUpFee":"b"}]}

        r = json.loads(backgroundSave(p,esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("fail",r['status'])

        #save to user that does not exist
        p = {"payoutList" : [{"id":esdu.id + 50,"earnings":6.23,"showUpFee":7.00}]}

        r = json.loads(backgroundSave(p,esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("fail",r['status'])

        #save junk
        p = {"payoutList" : [{"id":esdu.id + 50,"showUpFee":7.00}]}

        r = json.loads(backgroundSave(p,esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("fail",r['status'])

    #test bump all
    def testBumpAll(self):
        """Test bump all""" 
        logger = logging.getLogger(__name__)

        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        profile_consent_form = ProfileConsentForm(my_profile=self.u2.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        profile_consent_form = ProfileConsentForm(my_profile=self.u3.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        esd1 = self.es1.ESD.first()
        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()
        esdu2 = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u2.id).first()

        #bump all attended subjects
        r = json.loads(attendSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status'])   

        r = json.loads(bumpAll({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()
        esdu2 = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u2.id).first()
        self.assertEquals(esdu.bumped,True)
        self.assertEquals(esdu2.bumped,False)

        #junk data
        r = json.loads(bumpAll({},esd1.id+50,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("fail",r['status'])
    
    #test auto bump
    def testAutoBump(self):
        """Test auto bump""" 
        logger = logging.getLogger(__name__)

        esd1 = self.es1.ESD.first()
        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()
        esdu2 = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u2.id).first()

        self.assertEquals(esdu.bumped,False)
        self.assertEquals(esdu2.bumped,False)

        #try auto bump subjects that were previously bumped
        r = json.loads(cancelAcceptInvitation({"id":self.es1.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])

        r = json.loads(cancelAcceptInvitation({"id":self.es1.id},self.u2).content.decode("UTF-8"))
        self.assertFalse(r['failed'])

        d_now = self.d_now

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now.strftime("%#m/%#d/%Y") + ' 01:00 am -0000'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'},{'name': 'custom_reminder_time', 'value': 'false'}, {'name': 'reminder_time', 'value': '01/05/2021 12:04 pm -0800'}], 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esdu.confirmed=True
        esdu.save()

        esdu2.confirmed=True
        esdu2.save()

        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        profile_consent_form = ProfileConsentForm(my_profile=self.u2.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        r = json.loads(attendSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status'])

        r = json.loads(attendSubject({"id":esdu2.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status'])

        r = json.loads(bumpAll({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        esd2 = self.es2.ESD.first()
        r = json.loads(acceptInvitation({"id":self.es2.id},self.u).content.decode("UTF-8"))
        self.assertFalse(r['failed'])

        r = json.loads(acceptInvitation({"id":self.es2.id},self.u2).content.decode("UTF-8"))
        self.assertFalse(r['failed'])

        r = json.loads(autoBump({},esd2.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd2.id,user__id = self.u.id).first()
        esdu2 = experiment_session_day_users.objects.filter(experiment_session_day__id = esd2.id,user__id = self.u2.id).first()

        self.assertEquals(esdu.bumped,False)
        self.assertEquals(esdu2.bumped,False)

        #bump 1 of two
        esd1 = self.es1.ESD.first()
        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()
        esdu2 = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u2.id).first()

        # r = json.loads(noShowSubject({"id":esdu.id},esd1.id).content.decode("UTF-8"))
        # self.assertEquals("success",r['status'])

        # r = json.loads(noShowSubject({"id":esdu2.id},esd1.id).content.decode("UTF-8"))
        # self.assertEquals("success",r['status'])

        r = json.loads(attendSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status'])

        r = json.loads(attendSubject({"id":esdu2.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertIn("is now attending",r['status'])

        r = json.loads(autoBump({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()
        esdu2 = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u2.id).first()

        self.assertEquals(True if esdu.bumped != esdu2.bumped else False,True)

        #bump 0 of two
        esd1 = self.es1.ESD.first()
        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()
        esdu2 = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u2.id).first()

        r = json.loads(noShowSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        r = json.loads(noShowSubject({"id":esdu2.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        r = json.loads(autoBump({},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()
        esdu2 = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u2.id).first()

        self.assertEquals(esdu.bumped,False)
        self.assertEquals(esdu2.bumped,False)

        #test junk input
        r = json.loads(noShowSubject({"id":esdu.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        r = json.loads(noShowSubject({"id":esdu2.id},esd1.id,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("success",r['status'])

        r = json.loads(autoBump({},esd2.id+50,self.staff_u).content.decode("UTF-8"))
        self.assertEquals("fail",r['status'])

        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u.id).first()
        esdu2 = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u2.id).first()

        self.assertEquals(esdu.bumped,False)
        self.assertEquals(esdu2.bumped,False)

    #test earnings upload
    def test_earnings_upload(self):
        """Test earnings upload""" 
        logger = logging.getLogger(__name__)

        profile_consent_form = ProfileConsentForm(my_profile=self.u.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        profile_consent_form = ProfileConsentForm(my_profile=self.u2.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        profile_consent_form = ProfileConsentForm(my_profile=self.u3.profile, consent_form=self.es1.consent_form)
        profile_consent_form.save()

        esd1 = self.es1.ESD.first()

        #check empty upload
        my_str = ''
        buff = io.BytesIO(str.encode(my_str))
        #buff.seek(0,2)

        file_data = InMemoryUploadedFile(buff,'file', 'myfile.txt' , None, buff.tell(), None)

        r = json.loads(takeEarningsUpload(file_data, esd1.id, self.staff_u, 'false').content.decode("UTF-8"))
        self.assertEqual(r['message'], "Error: Empty list")

        #malformed list
        my_str = 'asdfasdf'
        buff = io.BytesIO(str.encode(my_str))
        #buff.seek(0,2)

        file_data = InMemoryUploadedFile(buff,'file', 'myfile.txt' , None, buff.tell(), None)

        r = json.loads(takeEarningsUpload(file_data, esd1.id, self.staff_u, 'false').content.decode("UTF-8"))
        self.assertIn("Failed to load earnings: invalid literal", r['message'])

        #add user
        my_str = '00121212,25,3\n00123456,14,2'
        buff = io.BytesIO(str.encode(my_str))
        #buff.seek(0,2)

        file_data = InMemoryUploadedFile(buff,'file', 'myfile.txt' , None, buff.tell(), None)

        r = json.loads(takeEarningsUpload(file_data, esd1.id, self.staff_u, 'true').content.decode("UTF-8"))
        self.assertIn("Earnings Imported", r['message'])

        esdu = experiment_session_day_users.objects.filter(experiment_session_day__id = esd1.id,user__id = self.u3.id).first()
        self.assertEquals(esdu.attended, True)
        self.assertEquals(esdu.earnings, 25)
        self.assertEquals(esdu.show_up_fee, 3)

















        


