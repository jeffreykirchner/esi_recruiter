from django.test import TestCase

from django.contrib.auth.models import User
from main.views.profileCreate import profileCreateUser
from main.models import genders,experiments,subject_types,account_types,majors,\
                        parameters,accounts,departments,locations,institutions,schools,email_filters
from main.views.staff.experimentSearchView import createExperimentBlank
from main.views.staff.experimentView import addSessionBlank
import logging

# Create your tests here.
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
       
        u_list = es_women_only.getValidUserList([],False,0,0,[])
        c=len(u_list)

        self.assertEqual(c, len(genders.objects.filter(name="Female")))

    def testAll(self):
        """Test all genders are recruited""" 

        e=experiments.objects.first()

        es_all = addSessionBlank(e)    
        es_all.recruitment_params.reset_settings()
        es_all.recruitment_params.gender.set(genders.objects.all())
        es_all.recruitment_params.subject_type.set(subject_types.objects.filter(id=1))

        u_list = es_all.getValidUserList([],False,0,0,[])
        c=len(u_list)
               
        self.assertEqual(c, len(genders.objects.all()))

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
    
    def testGenders(self):
        """Test subject types""" 
        logger = logging.getLogger(__name__)
        
        e=experiments.objects.first()

        #women only test
        es_women_only = addSessionBlank(e)    
        es_women_only.recruitment_params.reset_settings()
        es_women_only.recruitment_params.gender.set(genders.objects.filter(name="Female"))
        es_women_only.recruitment_params.subject_type.set(subject_types.objects.filter(id=1))
       
        u_list = es_women_only.getValidUserList([],False,0,0,[])
        c=len(u_list)

        self.assertEqual(c, len(genders.objects.filter(name="Female")))  
        