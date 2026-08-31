import pytest
from datetime import date, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from apps.accounts.models import Contact, PasswordResetOTP 

User = get_user_model()

@pytest.mark.django_db
def test_create_user():
    """
    Test 1:to make sure we can create a user 
    with custom fields like full name, gender, and date of birth.
    """
    amit_user = User.objects.create_user(
        username="amit_99",
        email="amit.sharma@gmail.com",
        password="password@123",
        full_name="Amit Sharma",
        gender="M",
        date_of_birth=date(1998, 5, 15)
    )
    
    assert amit_user.username == "amit_99"
    assert amit_user.full_name == "Amit Sharma"
    assert amit_user.gender == "M"
    assert amit_user.date_of_birth == date(1998, 5, 15)
    assert str(amit_user) == "amit_99"

@pytest.mark.django_db
def test_user_optional_fields_are_empty_by_default():
    """
    Test 2: Making sure optional fields remain blank strings 
    or None when they are not provided during user creation.
    """
    priya_user = User.objects.create_user(
        username="priya_dev",
        email="priya@yahoo.com",
        password="securepass123",
        gender="F"
    )
    assert priya_user.bio == ""
    assert priya_user.website == ""
    assert priya_user.phone_number == ""
    assert priya_user.full_name == ""
    assert not priya_user.profile_pic
    assert priya_user.date_of_birth is None


@pytest.mark.django_db
def test_user_saving_all_optional_profile_data():
    """
    Test 3: Checking if textareas like bio and custom text strings like
    Indian phone numbers save properly into the database records.
    """
    rahul_user = User.objects.create_user(
        username="rahul_mumbai",
        email="rahul@mumbai.in",
        password="mumbaipassword",
        full_name="Rahul Verma",
        gender="M",
        bio="Software Engineer from Mumbai, India.",
        website="https://rahulverma.dev",
        phone_number="+919876543210"
    )
    
    assert rahul_user.bio == "Software Engineer from Mumbai, India."
    assert rahul_user.website == "https://rahulverma.dev"
    assert rahul_user.phone_number == "+919876543210"

@pytest.mark.django_db
def test_one_user_can_follow_another_user():
    """
    Test 4: Tests if the follow relationship (Contact model) works 
    and checks if users are added to follower/following lists.
    """
    user_amit = User.objects.create_user(username="amit", email="a@test.com", password="123")
    user_priya = User.objects.create_user(username="priya", email="p@test.com", password="123")
    follow_record = Contact.objects.create(user_from=user_amit, user_to=user_priya)
    assert str(follow_record) == "amit follows priya"
    assert user_priya in user_amit.following.all()
    assert user_amit in user_priya.followers.all()


@pytest.mark.django_db
def test_cannot_follow_same_person_twice_constraint():
    """
    Test 5: Testing the UniqueConstraint. A user must not be 
    allowed to follow the exact same target account twice.
    """
    user_amit = User.objects.create_user(username="amit", email="a@test.com", password="123")
    user_priya = User.objects.create_user(username="priya", email="p@test.com", password="123")
    Contact.objects.create(user_from=user_amit, user_to=user_priya)
    try:
        Contact.objects.create(user_from=user_amit, user_to=user_priya)
        assert False, "Database did not catch the duplicate entry violation!"
    except IntegrityError:
        assert True

@pytest.mark.django_db
def test_generating_new_otp_deletes_older_tokens():
    """
    Test 6: Tests that creating a fresh token completely deletes 
    any older token for security, keeping maximum 1 token active per user.
    """
    user_amit = User.objects.create_user(username="amit", email="a@test.com", password="123")
    
    token_one = PasswordResetOTP.generate_otp(user_amit)
    assert PasswordResetOTP.objects.filter(user=user_amit).count() == 1
    token_two = PasswordResetOTP.generate_otp(user_amit)
    assert PasswordResetOTP.objects.filter(user=user_amit).count() == 1
    assert len(token_two.otp) == 6
    assert token_two.id != token_one.id


@pytest.mark.django_db
def test_otp_token_is_valid_immediately():
    """
    Test 7: A fresh token should evaluate to True right away.
    """
    user_amit = User.objects.create_user(username="amit", email="a@test.com", password="123")
    token = PasswordResetOTP.generate_otp(user_amit)
    assert token.is_valid() == True


@pytest.mark.django_db
def test_otp_token_expires_after_five_minutes():
    """
    Test 8: Trainee strategy to check expiration without mock systems.
    We alter the database row's timestamp to simulate time passing.
    """
    user_amit = User.objects.create_user(username="amit", email="a@test.com", password="123")
    token = PasswordResetOTP.generate_otp(user_amit)
    token.created_at = timezone.now() - timedelta(minutes=6)
    token.save() 
    assert token.is_valid() == False
