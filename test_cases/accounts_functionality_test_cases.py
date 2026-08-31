from django.core.files.uploadedfile import SimpleUploadedFile
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from apps.accounts.class_view import RegisterView, LoginVIew, VerifyOtp, RequestOtp
from apps.accounts.models import PasswordResetOTP, CustomUser, Contact
from apps.post.models import SocialPost, Story
from django.test import TestCase
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware

User = get_user_model()
ORIGINAL_REG_GET = RegisterView.get
ORIGINAL_LOGIN_GET = LoginVIew.get

@pytest.mark.django_db
def test_register_view_get_request_loads_page(client, monkeypatch):
    def mock_render(request, template_name, context=None, *args, **kwargs):
        return HttpResponse("Template processed natively and form loaded", status=200)
    monkeypatch.setattr("apps.accounts.class_view.render", mock_render)
    response = client.get(reverse('register'))
    assert response.status_code == 200
    assert b"form loaded" in response.content


@pytest.mark.django_db
def test_register_post_success(client):
    """Runs real view logic for registration success pathway."""
    valid_payload = {
        'username': 'rahul_dev_mumbai',
        'email': 'rahul.mumbai@gmail.com',
        'password': 'Password@123',
        'full_name': 'Rahul Sharma',
        'date_of_birth': '2000-01-15'
    }
    response = client.post(reverse('register'), data=valid_payload)
    
    assert response.status_code == 200
    assert response.json()['success'] is True
    assert User.objects.filter(username='rahul_dev_mumbai').exists() is True


@pytest.mark.django_db
def test_register_post_validation_error(client):
    """Runs real view logic for registration failure pathway."""
    invalid_payload = {
        'username': '',
        'email': 'bad-email',
    }
    response = client.post(reverse('register'), data=invalid_payload)
    
    assert response.status_code == 400
    assert response.json()['success'] is False


@pytest.mark.django_db
def test_login_view_get_method(client, monkeypatch):
    """Condition 1: GET request tracks normal page delivery (Covers lines 57-58)."""
    def mock_render(request, template_name, context=None, *args, **kwargs):
        return HttpResponse("Login form loaded natively", status=200)
    monkeypatch.setattr("apps.accounts.class_view.render", mock_render)
    response = client.get(reverse('login'))
    assert response.status_code == 200
    assert b"Login form loaded" in response.content


@pytest.mark.django_db
def test_login_post_standard_success(client):
    """Condition 2: Valid login -> Standard browser redirect status 302."""
    username_to_test = 'akash_login_user'
    if not User.objects.filter(username=username_to_test).exists():
        User.objects.create_user(username=username_to_test, email='akash@thoughtwin.com', password='SecurePassword@123')

    payload = {
        'username': username_to_test,
        'password': 'SecurePassword@123'
    }
    response = client.post(reverse('login'), data=payload)
    assert response.status_code == 302


@pytest.mark.django_db
def test_login_post_ajax_success(client):
    """Condition 3: Valid login via AJAX -> Returns JSON with redirect_url (Covers lines 69-72)."""
    username_to_test = 'akash_ajax_user'
    
    if not User.objects.filter(username=username_to_test).exists():
        User.objects.create_user(username=username_to_test, email='ajax@thoughtwin.com', password='SecurePassword@123')

    payload = {
        'username': username_to_test,
        'password': 'SecurePassword@123'
    }
    response = client.post(
        reverse('login'), 
        data=payload, 
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    
    assert response.status_code == 200
    json_data = response.json()
    assert json_data['success'] is True
    assert json_data['redirect_url'] == '/home'

@pytest.mark.django_db
def test_login_post_validation_error(client):
    """Condition 4: Empty fields -> Form fails validation and returns status 400."""
    invalid_payload = {
        'username': '',
        'password': ''
    }
    response = client.post(reverse('login'), data=invalid_payload)
    
    assert response.status_code == 400
    json_data = response.json()
    assert json_data['success'] is False
    assert 'errors' in json_data

@pytest.mark.django_db
def test_login_post_invalid_credentials_branch(client, monkeypatch):
    """
    Covers the authenticate() -> None branch in LoginVIew.post()
    without modifying the production view.
    """
    User.objects.create_user(
        username='invalid_login_user',
        email='invalid@login.com',
        password='CorrectPassword@123'
    )
    def mock_authenticate(*args, **kwargs):
        return None
    monkeypatch.setattr(
        "apps.accounts.class_view.authenticate",
        mock_authenticate
    )
    response = client.post(
        reverse('login'),
        data={
            'username': 'invalid_login_user',
            'password': 'WrongPassword@123'
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert data['success'] is False
    assert 'errors' in data


@pytest.mark.django_db
def test__otp_view_get_method(client, monkeypatch):
    """Condition 1: GET request path delivery check, safely mocking templates."""
    def mock_render(request, template_name, context=None, *args, **kwargs):
        return HttpResponse("OTP request form loaded natively", status=200)

    monkeypatch.setattr("apps.accounts.class_view.render", mock_render)

    response = client.get(reverse('request_otp')) 
    assert response.status_code == 200
    assert b"OTP request form loaded" in response.content


@pytest.mark.django_db
def test_otp_view_ajax_post_success(client, monkeypatch):
    """
    Condition 2: Valid email address submitted via AJAX. 
    Mocks SMTP mail transport out to completely test session and OTP generation logic.
    """
    email_to_test = "amit.sharma@thoughtwin.com"
    if not User.objects.filter(email=email_to_test).exists():
        User.objects.create_user(username="amit_sharma_9", email=email_to_test, password="Password@123")

    mail_sent_tracking = []
    def mock_send_mail(subject, message, from_email, recipient_list, *args, **kwargs):
        mail_sent_tracking.append({
            'subject': subject,
            'recipient': recipient_list[0]
        })
        return 1 

    monkeypatch.setattr("apps.accounts.class_view.send_mail", mock_send_mail)
    payload = {'email': email_to_test}
    response = client.post(
        reverse('request_otp'), 
        data=payload, 
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data['success'] is True
    assert json_data['redirect_url'] == 'verify-otp/'
    assert client.session['reset_email'] == email_to_test
    assert PasswordResetOTP.objects.filter(user__email=email_to_test).exists() is True
    assert len(mail_sent_tracking) == 1
    assert mail_sent_tracking[0]['recipient'] == email_to_test

@pytest.mark.django_db
def test_request_otp_get(client):
    response = client.get(reverse("request_otp"))
    assert response.status_code == 200
    assert "form" in response.context

@pytest.mark.django_db
def test_request_otp_standard_post_success(client, monkeypatch):
    email = "standard.otp@test.com"
    User.objects.create_user(username="standard_otp_user",
        email=email, password="Password@123"
    )
    monkeypatch.setattr(
        "apps.accounts.class_view.send_mail",
        lambda *args, **kwargs: 1
    )
    response = client.post(reverse('request_otp'), data={'email': email})
    assert response.status_code == 302
    assert response.url == '/home/'
    assert client.session['reset_email'] == email
    assert PasswordResetOTP.objects.filter(
        user__email=email
    ).exists()

@pytest.mark.django_db
def test_request_otp_view_post_user_not_found_error(client):
    """
    Condition 3: Submitting an email format that passes basic validation 
    but has no matching account in the database (Tests your view's inner 'else' branch).
    """
    non_existent_email = "notfound@thoughtwin.com"
    User.objects.filter(email=non_existent_email).delete()

    payload = {'email': non_existent_email}
    
    response = client.post(
        reverse('request_otp'), 
        data=payload, 
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    assert response.status_code == 400
    json_data = response.json()
    assert json_data['success'] is False
    assert 'email' in json_data['errors']


@pytest.mark.django_db
def test_request_otp_view_ajax_post_invalid_form_error(client):
    """
    Condition 4: Empty payload or completely missing fields.
    Triggers the outer validation failure blocks to return status 400.
    """
    invalid_payload = {'email': ''}
    
    response = client.post(
        reverse('request_otp'), 
        data=invalid_payload, 
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    
    assert response.status_code == 400
    json_data = response.json()
    assert json_data['success'] is False
    assert 'errors' in json_data

@pytest.mark.django_db
def test_request_otp_standard_post_user_not_found():
    """
    Covers RequestOtp.post() user-not-found branch for a normal
    non-AJAX request.

    The production view intentionally reaches the end and returns None
    for this branch, so RequestFactory is used instead of Django Client.
    """
    email = 'missing.standard@test.com'
    User.objects.filter(email=email).delete()
    factory = RequestFactory()
    request = factory.post(
        reverse('request_otp'),
        data={'email': email}
    )
    middleware = SessionMiddleware(lambda request: None)
    middleware.process_request(request)
    request.session.save()

    response = RequestOtp.as_view()(request)
    assert response is None

@pytest.mark.django_db
def test_verify_otp_view_get_method(client, monkeypatch):
    """Condition 1: GET path delivery check, safely mocking templates."""
    def mock_render(request, template_name, context=None, *args, **kwargs):
        return HttpResponse("Verify OTP form loaded natively", status=200)

    monkeypatch.setattr("apps.accounts.class_view.render", mock_render)

    response = client.get(reverse('verify_otp')) 
    assert response.status_code == 200
    assert b"Verify OTP form loaded" in response.content


@pytest.mark.django_db
def test_verify_otp_missing_session_ajax_error(client):
    """Condition 2: Session lacks an email token -> Fails with expired session code 400."""
    response = client.post(
        reverse('verify_otp'),
        data={'otp': '123456', 'new_password': 'NewPassword@123'},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    
    assert response.status_code == 400
    assert response.json()['success'] is False
    assert "Session expired" in response.json()['message']


@pytest.mark.django_db
def test_verify_otp_missing_session_standard_redirect(client):
    """Condition 3: Standard browser post with a missing session -> Redirects to request page (302)."""
    response = client.post(
        reverse('verify_otp'),
        data={'otp': '123456', 'new_password': 'NewPassword@123'}
    )
    assert response.status_code == 302


@pytest.mark.django_db
def test_verify_otp_ajax_success_path(client):
    """
    Condition 4: Valid OTP token -> Updates password, purges the token row, 
    flushes the session profile, and redirects to login with status 200.
    """
    email_to_test = "akash.verify@thoughtwin.com"
    user = User.objects.create_user(username="akash_verify", email=email_to_test, password="OldPassword@123")
    otp_record = PasswordResetOTP.generate_otp(user)
    otp_code = otp_record.otp
    session = client.session
    session['reset_email'] = email_to_test
    session.save()

    payload = {
        'otp': otp_code,
        'new_password': 'BrandNewIndianPassword@123'
    }
    response = client.post(
        reverse('verify_otp'),
        data=payload,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    assert response.status_code == 200
    assert response.json()['success'] is True
    assert "login" in response.json()['redirect_url']
    assert PasswordResetOTP.objects.filter(id=otp_record.id).exists() is False
    assert 'reset_email' not in client.session
    from django.contrib.auth import authenticate
    assert authenticate(username="akash_verify", password="BrandNewIndianPassword@123") == user


@pytest.mark.django_db
def test_verify_otp_invalid_or_expired_error(client):
    """Condition 5: Invalid OTP string passed -> Returns mismatch message with status 400."""
    email_to_test = "akash.verify@thoughtwin.com"
    user = User.objects.create_user(username="akash_verify", email=email_to_test, password="OldPassword@123")
    PasswordResetOTP.generate_otp(user)

    session = client.session
    session['reset_email'] = email_to_test
    session.save()

    payload = {
        'otp': '000000',
        'new_password': 'BrandNewPassword@123'
    }

    response = client.post(
        reverse('verify_otp'),
        data=payload,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )

    assert response.status_code == 400
    assert response.json()['success'] is False
    assert "Invalid or expired OTP" in response.json()['message']

@pytest.mark.django_db
def test_verify_otp_standard_success(client):
    email = "standard.verify@test.com"
    user = User.objects.create_user(
        username="standard_verify_user",
        email=email,
        password="OldPassword@123"
    )
    otp_record = PasswordResetOTP.generate_otp(user)
    session = client.session
    session['reset_email'] = email
    session.save()
    response = client.post(
        reverse('verify_otp'),
        data={
            'otp': otp_record.otp,
            'new_password': 'NewPassword@123'
        }
    )
    assert response.status_code == 302
    assert response.url == reverse('login')
    user.refresh_from_db()
    from django.contrib.auth import authenticate
    assert authenticate(
        username='standard_verify_user',
        password='NewPassword@123'
    ) == user

@pytest.mark.django_db
def test_verify_otp_standard_invalid_otp(client, monkeypatch):
    email = "standard.invalid@test.com"

    user = User.objects.create_user(
        username="standard_invalid_otp",
        email=email,
        password="OldPassword@123"
    )

    PasswordResetOTP.generate_otp(user)

    session = client.session
    session['reset_email'] = email
    session.save()
    captured_messages = []

    def mock_error(request, message, *args, **kwargs):
        captured_messages.append(message)

    monkeypatch.setattr(
        "apps.accounts.class_view.messages.error",
        mock_error
    )
    factory = RequestFactory()

    request = factory.post(
        reverse('verify_otp'),
        data={
            'otp': '000000',
            'new_password': 'NewPassword@123'
        }
    )
    middleware = SessionMiddleware(lambda request: None)
    middleware.process_request(request)
    request.session['reset_email'] = email
    request.session.save()
    response = VerifyOtp.as_view()(request)
    assert response is None

    assert "Invalid or expired OTP." in captured_messages


@pytest.mark.django_db
def test_verify_otp_user_does_not_exist_exception(client):
    """Condition 6: Valid session structure but user row is missing -> Caught by exception try-catch."""
    session = client.session
    session['reset_email'] = 'ghost.user@thoughtwin.com'
    session.save()
    payload = {
        'otp': '111111',
        'new_password': 'BrandNewPassword@123'
    }
    response = client.post(
        reverse('verify_otp'),
        data=payload,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    assert response.status_code == 400
    assert response.json()['success'] is False
    assert "An error occurred" in response.json()['message']

@pytest.mark.django_db
def test_verify_otp_standard_user_does_not_exist(client, monkeypatch):
    email = 'doesnotexist@test.com'
    session = client.session
    session['reset_email'] = email
    session.save()
    captured_messages = []
    def mock_error(request, message, *args, **kwargs):
        captured_messages.append(message)
    monkeypatch.setattr(
        "apps.accounts.class_view.messages.error",
        mock_error
    )
    factory = RequestFactory()
    request = factory.post(
        reverse('verify_otp'),
        data={
            'otp': '111111',
            'new_password': 'NewPassword@123'
        }
    )
    middleware = SessionMiddleware(lambda request: None)
    middleware.process_request(request)
    request.session['reset_email'] = email
    request.session.save()
    response = VerifyOtp.as_view()(request)
    assert response is None
    assert "An error occurred." in captured_messages



class HomeViewIntegrationTests(TestCase):
    def setUp(self):
        """Set up standard integration environment records."""
        self.user = User.objects.create_user(
            username='testuser', 
            password='password123'
        )
        self.url = reverse('home')

    def test_anonymous_user_cannot_see_page(self):
        """1. Integration: Verify that Auth Middleware redirects unauthenticated clients."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_logged_in_user_can_see_page(self):
        """Verify authenticated users can access the home page."""
        self.client.login(
            username='testuser',
            password='password123'
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context)


    def test_pagination_shows_two_posts_per_page(self):
        """Verify home page pagination returns two posts per page."""
        self.client.login(username='testuser', password='password123')
        SocialPost.objects.create(author=self.user, content="Oldest post")
        SocialPost.objects.create(author=self.user, content="Middle post")
        SocialPost.objects.create(author=self.user, content="Newest post")
        response = self.client.get(self.url, {'page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context)

    def test_home_page_includes_recent_stories(self):
        self.client.login(username='testuser', password='password123')
        image = SimpleUploadedFile(
            "recent_story.jpg", b"fake-image-content", content_type="image/jpeg"
        )
        story = Story.objects.create(author=self.user, image=image)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context)
        stories = response.context['stories']
        self.assertTrue(stories.filter(id=story.id).exists())
        returned_story = stories.get(id=story.id)
        self.assertEqual(returned_story.author, self.user)
        self.assertTrue(returned_story.image)
        self.assertTrue(returned_story.image.name)
        self.assertTrue(returned_story.image.name.lower().endswith('.jpg'))


class LogoutViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='logout_test_user', password='password123')
        self.url = reverse('logout')

    def test_logout_user(self):
        self.client.login(username='logout_test_user', password='password123')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))

    def test_logout_clears_session(self):
        self.client.login(username='logout_test_user', password='password123')
        self.assertIn('_auth_user_id', self.client.session)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)

class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.other_user = User.objects.create_user(username='otheruser', password='password123')
        self.url = reverse('profile_view', kwargs={'username': 'testuser'})

    def test_profile_view_redirects_when_username_is_different(self):
        user1 = User.objects.create_user(
            username="profile_user_1",
            email="profile1@test.com",
            password="password123"
        )

        User.objects.create_user(
            username="profile_user_2",
            email="profile2@test.com",
            password="password123"
        )

        self.client.force_login(user1)

        response = self.client.get(
            reverse(
                "profile_view",
                kwargs={"username": "profile_user_2"}
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            response.url,
            reverse(
                "profile_view",
                kwargs={"username": "profile_user_1"}
            )
        )


    def test_user_can_view_own_profile(self):
        self.client.login(username='testuser', password='password123')
        SocialPost.objects.create(author=self.user, content='My first post')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['profile_user'], self.user)
        self.assertEqual(response.context['posts'].count(), 1)

    def test_user_cannot_view_other_profile(self):
        self.client.login(username='testuser', password='password123')
        url = reverse('profile_view', kwargs={'username': 'otheruser'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
            reverse('profile_view', kwargs={'username': 'testuser'})
        )

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


class EditProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.login(username='testuser', password='password123')
        self.url = reverse('edit_profile')
    

    def test_edit_profile_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_edit_profile_post(self):
        data = {
            'full_name': 'Rahul Sharma',
            'bio': 'I am a developer',
            'website': 'https://example.com',
            'phone_number': '9876543210',
            'gender': 'M',
            'date_of_birth': '2000-01-15'
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
            reverse('profile_view', kwargs={'username': 'testuser'})
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, 'Rahul Sharma')
        self.assertEqual(self.user.bio, 'I am a developer')
        self.assertEqual(self.user.website, 'https://example.com')
        self.assertEqual(self.user.phone_number, '9876543210')
        self.assertEqual(self.user.gender, 'M')
        self.assertEqual(str(self.user.date_of_birth), '2000-01-15')

    def test_edit_profile_with_profile_picture(self):
        image = SimpleUploadedFile('profile.jpg',
            b'fake image content',
            content_type='image/jpeg'
        )
        data = {
            'full_name': 'Rahul Sharma',
            'bio': 'Updated bio',
            'website': 'https://example.com',
            'phone_number': '9876543210',
            'gender': 'M',
            'date_of_birth': '2000-01-15',
            'profile_pic': image
        }
        response = self.client.post(
            self.url,
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.profile_pic)
        self.assertEqual(self.user.full_name, 'Rahul Sharma')

    def test_edit_profile_without_date_of_birth(self):
        """
        Covers the branch where date_of_birth is not supplied.
        """
        data = {
            'full_name': 'Rahul Sharma',
            'bio': 'Developer',
            'website': 'https://example.com',
            'phone_number': '9876543210',
            'gender': 'M',
            'date_of_birth': ''
        }

        response = self.client.post(
            self.url,
            data
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                'profile_view',
                kwargs={'username': 'testuser'}
            )
        )

        self.user.refresh_from_db()

        self.assertEqual(self.user.full_name, 'Rahul Sharma')
        self.assertEqual(self.user.bio, 'Developer')
        self.assertEqual(self.user.website, 'https://example.com')
        self.assertEqual(self.user.phone_number, '9876543210')
        self.assertEqual(self.user.gender, 'M')



class ToggleFollowTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', password='password123')

        self.other_user = CustomUser.objects.create_user(username='otheruser',
            password='password123'
        )

        self.url = reverse('toggle_follow')
        self.client.login(username='testuser', password='password123')

    def test_missing_user_id(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')
        self.assertEqual(response.json()['message'], 'Missing user ID.')

    def test_follow_user(self):
        response = self.client.post(self.url, {'id': self.other_user.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['action'], 'follow')

        self.assertTrue(
            Contact.objects.filter(user_from=self.user, user_to=self.other_user).exists()
        )
 
    def test_unfollow_user(self):
        Contact.objects.create(user_from=self.user, user_to=self.other_user)

        response = self.client.post(self.url, {'id': self.other_user.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['action'], 'unfollow')
        self.assertFalse(
            Contact.objects.filter(user_from=self.user, user_to=self.other_user).exists()
        )

    def test_cannot_follow_yourself(self):
        response = self.client.post(self.url, {'id': self.user.id})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')
        self.assertEqual(response.json()['message'], 'You cannot follow yourself.')

    def test_invalid_user_id(self):
        response = self.client.post(self.url, {'id': 999999})
        self.assertEqual(response.status_code, 404)