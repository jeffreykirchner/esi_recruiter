from django.test import TestCase

from django.contrib.auth.models import User

from main.views.profileCreate import profileCreateUser
from main.models import genders,experiments,subject_types,account_types,majors,\
                        parameters,accounts,departments,locations,institutions,schools,email_filters,\
                        experiment_session_day_users    
from main.views.staff.experimentSearchView import createExperimentBlank
from main.views.staff.experimentView import addSessionBlank
from main.views.staff.experimentSessionView import changeConfirmationStatus,updateSessionDay,cancelSession

from datetime import datetime,timedelta
import pytz
import logging
from django.db.models import Q,F

class subjectHomeTestCase(TestCase):

    e1 = None         #experiments
    e2 = None
    u=None            #user
    d_now = None      #date time now
    l1=None           #locations
    l2=None
    account1=None     #accounts   
    p=None            #parameters
    staff_u=None      #staff user

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

        self.u = profileCreateUser("u1@chapman.edu","u1@chapman.edu","zxcvb1234asdf","first","last","123456",\
                          genders.objects.first(),"7145551234",majors.objects.first(),\
                          subject_types.objects.get(id=1),False,True,account_types.objects.get(id=2))
        
        self.d_now = datetime.now(pytz.utc)
        d_now_plus_two = self.d_now + timedelta(days=2)
        d_now_plus_three = self.d_now + timedelta(days=3)
        
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
        self.assertEqual(es1.getConfirmedCount(),0)
