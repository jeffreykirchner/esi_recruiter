from django.contrib.auth.models import User
from main.models import profile

from django.utils.crypto import get_random_string

from main.views.registration import profileCreateUser

from main.models import genders
from main.models import SubjectTypes
from main.models import account_types
from main.models import majors

go=True

while go:
    print("***Manually Add Staff User***")
    print("Enter Email:")
    email = input()
    print("Enter First Name:")
    first_name = input()
    print("Enter Last Name:")
    last_name = input()

    user_name = email
    temp_st =  SubjectTypes.objects.get(id=3)
    new_user = profileCreateUser(email, email, get_random_string(16), first_name, last_name, "123456",\
                    genders.objects.last(),"7145551234", majors.objects.first(),\
                    temp_st, False, True, account_types.objects.get(id=1))

    new_user.profile.email_confirmed='yes'
    new_user.profile.save()
    new_user.profile.setup_email_filter()

    print(f"User {new_user.first_name} {new_user.last_name} created.")

    print("")
    print("Add another user? (y/n)")
    if input() != "y":
        go=False


        



                

