from django.test import TestCase
import unittest

from django.contrib.auth.models import User

from main.views.profileCreate import profileCreateUser
from main.models import genders,experiments,subject_types,account_types,majors,\
                        parameters,accounts,departments,locations,institutions,schools,email_filters,\
                        experiment_session_day_users,experiment_session_days

from main.views.staff.experimentSearchView import createExperimentBlank
from main.views.staff.experimentView import addSessionBlank
from main.views.staff.experimentSessionView import changeConfirmationStatus,updateSessionDay,cancelSession
from main.cron import checkForReminderEmails

from datetime import datetime,timedelta
import pytz
import logging
from django.db.models import Q,F
import json
import ast

class cronTests(TestCase):

    e1 = None         #experiments
    e2 = None

    es1 = None        #sessions 
    es2 = None

    u=None            #user
    u2=None

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

        #subject 1
        self.u = profileCreateUser("u1@chapman.edu","u1@chapman.edu","zxcvb1234asdf","first","last","00123456",\
                          genders.objects.first(),"7145551234",majors.objects.first(),\
                          subject_types.objects.get(id=1),False,True,account_types.objects.get(id=2))
        
        logger.info(self.u)

        self.u.is_active = True
        self.u.profile.email_confirmed = 'yes'
        self.u.profile.consent_required = False

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
        self.u2.profile.consent_required = False

        self.u2.profile.save()
        self.u2.save()

        self.u2.profile.setup_email_filter()
        
        #sessions
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

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_two.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'},{'name': 'custom_reminder_time', 'value': 'false'}, {'name': 'reminder_time', 'value': '01/05/2021 12:04 pm -0800'}], 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #add subject 1
        self.es1.addUser(self.u.id,self.staff_u,True)
        temp_esdu = esd1.experiment_session_day_users_set.filter(user__id = self.u.id).first()
        r = json.loads(changeConfirmationStatus({"userId":self.u.id,"confirmed":"confirm","esduId":temp_esdu.id},self.es1.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #add subject 2
        self.es1.addUser(self.u2.id,self.staff_u,True)
        temp_esdu = esd1.experiment_session_day_users_set.filter(user__id = self.u2.id).first()
        r = json.loads(changeConfirmationStatus({"userId":self.u2.id,"confirmed":"unconfirm","esduId":temp_esdu.id},self.es1.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

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
        esd2 = self.es2.ESD.first()

        session_day_data={'status': 'updateSessionDay', 'id': esd2.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_plus_three.strftime("%#m/%#d/%Y") + ' 04:00 pm -0700'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'},{'name': 'custom_reminder_time', 'value': 'false'}, {'name': 'reminder_time', 'value': '01/05/2021 12:04 pm -0800'}], 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #add subject 1
        self.es2.addUser(self.u.id,self.staff_u,True)
        temp_esdu = esd2.experiment_session_day_users_set.filter(user__id = self.u.id).first()
        r = json.loads(changeConfirmationStatus({"userId":self.u.id,"confirmed":"unconfirm","esduId":temp_esdu.id},self.es2.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #add subject 2
        self.es2.addUser(self.u2.id,self.staff_u,True)
        temp_esdu = esd2.experiment_session_day_users_set.filter(user__id = self.u2.id).first()
        r = json.loads(changeConfirmationStatus({"userId":self.u2.id,"confirmed":"confirm","esduId":temp_esdu.id},self.es1.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

    #test that cron reminder
    def testReminderEmail(self):
        """Test cron reminder email""" 
        logger = logging.getLogger(__name__)

        esd1 = self.es1.ESD.first()

        esd1.experiment_session.canceled=True
        esd1.experiment_session.save()

        #send to canceled session
        r = esd1.sendReminderEmail()
        logger.info(r)

        self.assertEquals("fail",r['status'])

        #one user confirmed one not
        esd1 = self.es1.ESD.first()
        esd1.experiment_session.canceled=False
        esd1.experiment_session.save()

        r = esd1.sendReminderEmail()
        logger.info(r)

        self.assertEquals("success",r['status'])
        self.assertEquals(1,len(r['emailList']))

        #send to session again
        esd1 = self.es1.ESD.first()
        r = esd1.sendReminderEmail()
        logger.info(r)

        self.assertEquals("fail",r['status'])

        #test cron job
        temp_esdu = esd1.experiment_session_day_users_set.filter(user__id = self.u.id).first()
        r = json.loads(changeConfirmationStatus({"userId":self.u.id,"confirmed":"unconfirm","esduId":temp_esdu.id},self.es1.id,False).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1.reminder_email_sent=False
        esd1.save()
        cj = checkForReminderEmails()

        d_now = self.d_now + timedelta(hours=23)
        
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now.strftime("%#m/%#d/%Y %I:%M %p ") + ' -0000'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'},{'name': 'custom_reminder_time', 'value': 'false'}, {'name': 'reminder_time', 'value': '01/05/2021 12:04 pm -0800'}], 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        #unsent experiment in 23 hours
        r = cj.do()
        #logger.info(r)
        self.assertEquals(1,len(r["standard"]))

        #sent experiment in 23 hours
        r = cj.do()
        self.assertEquals(0,len(r["standard"]))

        #unsent, 30 hours
        esd1 = self.es1.ESD.first()
        esd1.reminder_email_sent=False
        esd1.save()

        d_now = self.d_now + timedelta(hours=30)
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now.strftime("%#m/%#d/%Y %I:%M %p ") + ' -0000'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'},{'name': 'custom_reminder_time', 'value': 'false'}, {'name': 'reminder_time', 'value': '01/05/2021 12:04 pm -0800'}], 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        r = cj.do()
        self.assertEquals(0,len(r["standard"]))

        #unsent, 15 hours
        esd1 = self.es1.ESD.first()
        esd1.reminder_email_sent=False
        esd1.save()

        d_now = self.d_now + timedelta(hours=15)
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now.strftime("%#m/%#d/%Y %I:%M %p ") + ' -0000'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'},{'name': 'custom_reminder_time', 'value': 'false'}, {'name': 'reminder_time', 'value': '01/05/2021 12:04 pm -0800'}], 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        r = cj.do()
        self.assertEquals(0,len(r["standard"]))

        #unsent, 23 hours, canceled
        esd1 = self.es1.ESD.first()
        esd1.reminder_email_sent=False
        esd1.experiment_session.canceled=True
        esd1.experiment_session.save()
        esd1.save()

        d_now = self.d_now + timedelta(hours=23)
        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now.strftime("%#m/%#d/%Y %I:%M %p ") + ' -0000'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'},{'name': 'custom_reminder_time', 'value': 'false'}, {'name': 'reminder_time', 'value': '01/05/2021 12:04 pm -0800'}], 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        r = cj.do()
        self.assertEquals(0,len(r["standard"]))

        #custom time, within range
        esd1 = self.es1.ESD.first()
        esd1.reminder_email_sent=False
        esd1.experiment_session.canceled=False
        esd1.experiment_session.save()
        esd1.save()

        d_now = self.d_now-timedelta(hours=1)
        d_now_later = self.d_now + timedelta(hours=22)

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_later.strftime("%#m/%#d/%Y %I:%M %p ") + ' -0000'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'},{'name': 'custom_reminder_time', 'value': 'true'}, {'name': 'reminder_time', 'value': d_now.strftime("%#m/%#d/%Y %I:%M %p ") + ' -0000'}], 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1 = self.es1.ESD.first()
        #logger.info(f"Custom cron test: reminder time {esd1.reminder_time} date {esd1.date} custom reminder time {esd1.custom_reminder_time}")

        r = cj.do()
        self.assertEquals(0,len(r["standard"]))
        self.assertEquals(1,len(r["custom"]))

        #custom time, outside range
        esd1 = self.es1.ESD.first()
        esd1.reminder_email_sent=False
        esd1.experiment_session.canceled=False
        esd1.experiment_session.save()
        esd1.save()

        d_now = self.d_now-timedelta(hours=5)
        d_now_later = self.d_now + timedelta(hours=22)

        session_day_data={'status': 'updateSessionDay', 'id': esd1.id, 'formData': [{'name': 'location', 'value': str(self.l1.id)}, {'name': 'date', 'value': d_now_later.strftime("%#m/%#d/%Y %I:%M %p ") + ' -0000'}, {'name': 'length', 'value': '60'}, {'name': 'account', 'value': str(self.account1.id)}, {'name': 'auto_reminder', 'value': 'true'},{'name': 'enable_time', 'value': 'true'},{'name': 'custom_reminder_time', 'value': 'true'}, {'name': 'reminder_time', 'value': d_now.strftime("%#m/%#d/%Y %I:%M %p ") + ' -0000'}], 'sessionCanceledChangedMessage': False}
        r = json.loads(updateSessionDay(session_day_data,esd1.id).content.decode("UTF-8"))
        self.assertEqual(r['status'],"success")

        esd1 = self.es1.ESD.first()
        #logger.info(f"Custom cron test: reminder time {esd1.reminder_time} date {esd1.date} custom reminder time {esd1.custom_reminder_time}")

        r = cj.do()
        self.assertEquals(0,len(r["standard"]))
        self.assertEquals(0,len(r["custom"]))




        








        


