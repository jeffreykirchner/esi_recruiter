from django.test import TestCase
from django.contrib.auth.models import User
from main.views.profileCreate import profileCreateUser
from main.models import genders,subject_types,account_types,majors

# Create your tests here.
class RecruiteTestCase(TestCase):
    def setUp(self):
        profileCreateUser("u1","u1@chapman.edu","zxcvb1234asdf","u","1","123456",\
                          genders.objects.get(id=1),"7145551234",majors.objects.first(),\
                          subject_types.objects.get(id=1),False,True,account_types.objects.get(id=2))
    
    def testGenders(self):
        """Test correct genders are recruited"""
        u = User.objects.filter(first_name="u").first()
        self.assertEqual(u.email, 'u1@chapman.edu2')