import json
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.api.api_views import (
    RegisterView,
    LoginView,
    HomeView,
    ProfileView,
    ToggleFollow,
    EditProfileView,
    LogoutAPIView,
    RequestOtp,
    VerifyOtp,
)
from apps.accounts.models import Contact


User = get_user_model()
class RegisterViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("apps.accounts.api.api_views.CustomUserSerializer")
    def test_register_success(self, mock_serializer):
        serializer = mock_serializer.return_value
        serializer.is_valid.return_value = True
        request = self.factory.post(
            "/register/",
            {"username": "newuser", "email": "newuser@test.com", "password": "Password@123"},
            format="json",
        )
        response = RegisterView.as_view()(request)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["redirect_url"], "/login/")
        serializer.is_valid.assert_called_once()
        serializer.save.assert_called_once()

    @patch("apps.accounts.api.api_views.CustomUserSerializer")
    def test_register_invalid(self, mock_serializer):
        serializer = mock_serializer.return_value
        serializer.is_valid.return_value = False
        serializer.errors = {"email": ["This email is already registered."]}
        request = self.factory.post(
            "/register/",
            {"username": "existing", "email": "existing@test.com", "password": "Password@123"},
            format="json",
        )
        response = RegisterView.as_view()(request)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("errors", data)
        serializer.save.assert_not_called()

class LoginViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="login_test_user", email="login@test.com", password="Password@123"
        )
    @patch("apps.accounts.api.api_views.RefreshToken.for_user")
    @patch("apps.accounts.api.api_views.UniversalLoginForm")
    def test_login_success(self,mock_form_class,mock_refresh_for_user):
        mock_form = mock_form_class.return_value
        mock_form.is_valid.return_value = True
        mock_form.user_cache = self.user
        mock_refresh = MagicMock()
        mock_refresh.access_token = "access-token"
        mock_refresh.__str__.return_value = "refresh-token"
        mock_refresh_for_user.return_value = mock_refresh

        request = self.factory.post(
            "/login/",
            {"username": "login_test_user", "password": "Password@123"},
            format="json",
        )
        response = LoginView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["access"], "access-token")
        self.assertEqual(data["refresh"], "refresh-token")
        self.assertEqual(data["redirect_url"], "/home")

    @patch("apps.accounts.api.api_views.UniversalLoginForm")
    def test_login_invalid(self, mock_form_class):
        mock_form = mock_form_class.return_value
        mock_form.is_valid.return_value = False
        mock_form.errors.get_json_data.return_value = {
            "username": [{"message": "Invalid login.", "code": "invalid"}]
        }

        request = self.factory.post(
            "/login/",
            {"username": "wronguser", "password": "wrongpassword"},
            format="json",
        )
        response = LoginView.as_view()(request)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)

        self.assertFalse(data["success"])
        self.assertIn("errors", data)
        self.assertIn("attempts_remaining", data["errors"],)

class HomeViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="home_user", email="home@test.com", password="Password@123"
        )

    @patch("apps.accounts.api.api_views.SocialPostSerializer")
    def test_home_success(self, mock_serializer):
        post_serializer = MagicMock()
        post_serializer.data = []
        mock_serializer.return_value = post_serializer
        request = self.factory.get("/home/")
        force_authenticate(request, user=self.user)
        response = HomeView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["User"], self.user.username)
        self.assertIn("posts", data)
        self.assertIn("stories", data)

class ProfileViewTests(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="profile_user", email="profile@test.com", password="Password@123"
        )

    @patch("apps.accounts.api.api_views.SocialPostSerializer")
    def test_profile_success(self, mock_serializer):
        mock_serializer.return_value.data = []
        request = self.factory.get(f"/profile/{self.user.username}/")
        force_authenticate(request, user=self.user)
        response = ProfileView.as_view()(request, username=self.user.username)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["profile_user"], self.user.username)
        self.assertIn("posts", data)

    def test_profile_wrong_username_redirects(self):
        request = self.factory.get("/profile/another_user/")
        force_authenticate(request, user=self.user)
        response = ProfileView.as_view()(request, username="another_user")

        self.assertEqual(response.status_code, 302)
        self.assertIn(self.user.username, response.url)

class ToggleFollowTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="follower", email="follower@test.com", password="Password@123"
        )
        self.target_user = User.objects.create_user(
            username="target", email="target@test.com", password="Password@123"
        )

    def test_toggle_follow_success(self):
        request = self.factory.post("/follow/", {"id": self.target_user.id,}, format="json")
        force_authenticate(request, user=self.user)
        response = ToggleFollow.as_view()(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["action"], "follow")
        self.assertEqual(data["follower_count"], 1)

        self.assertTrue(
            Contact.objects.filter(user_from=self.user, user_to=self.target_user).exists()
        )

    def test_toggle_unfollow_success(self):
        Contact.objects.create(user_from=self.user, user_to=self.target_user)
        request = self.factory.post(
            "/follow/", {"id": self.target_user.id}, format="json"
        )
        force_authenticate(request, user=self.user)
        response = ToggleFollow.as_view()(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["action"], "unfollow")
        self.assertEqual(data["follower_count"], 0)

    def test_toggle_follow_missing_id(self):
        request = self.factory.post("/follow/", {}, format="json")
        force_authenticate(request, user=self.user)
        response = ToggleFollow.as_view()(request)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["message"], "Missing user ID.")

    def test_toggle_follow_self(self):
        request = self.factory.post(
            "/follow/", {"id": self.user.id}, format="json"
        )
        force_authenticate(request, user=self.user)
        response = ToggleFollow.as_view()(request)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["message"], "You cannot follow yourself.")

class EditProfileViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="edit_user", email="edit@test.com", password="Password@123"
        )
        self.other_user = User.objects.create_user(
            username="other_edit_user", email="otheredit@test.com", password="Password@123"
        )

    def test_edit_profile_success(self):
        request = self.factory.post(
            f"/profile/edit/{self.user.id}/",
            {
                "full_name": "Updated Name",
                "bio": "Updated bio",
                "website": "https://example.com",
                "phone_number": "9876543210",
                "gender": "M",
                "date_of_birth": "2000-01-01",
            },
            format="multipart",
        )

        force_authenticate(request, user=self.user)
        response = EditProfileView.as_view()(request, user_id=self.user.id)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["username"], "Updated Name")
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Updated Name")
        self.assertEqual(self.user.bio, "Updated bio")

    def test_edit_profile_forbidden_for_other_user(self):
        request = self.factory.post(
            f"/profile/edit/{self.other_user.id}/",
            {"full_name": "Hacker"},
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = EditProfileView.as_view()(request, user_id=self.other_user.id)
        self.assertEqual(response.status_code, 403)
        data = response.data
        self.assertEqual(data["detail"], "You do not have permission to edit this profile.")

    def test_edit_profile_with_profile_picture(self):
        image = SimpleUploadedFile(
            "profile.jpg", b"fake-image-data", content_type="image/jpeg",
        )
        request = self.factory.post(
            f"/profile/edit/{self.user.id}/",
            {"full_name": "Picture User", "profile_pic": image},
            format="multipart",
        )
        force_authenticate(request, user=self.user)
        response = EditProfileView.as_view()(request, user_id=self.user.id,)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.profile_pic)

class LogoutAPIViewTests(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="logout_user", email="logout@test.com", password="Password@123"
        )

    def add_session_to_request(self, request):
        middleware = SessionMiddleware(lambda request: None)
        middleware.process_request(request)
        request.session.save()
        return request

    def test_logout_success(self):
        request = self.factory.post("/logout/")
        request = self.add_session_to_request(request)
        force_authenticate(request, user=self.user)
        response = LogoutAPIView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data["detail"], "Successfully logged out on server.")
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)


class RequestOtpTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="otp_user", email="otp@test.com", password="Password@123"
        )

    @patch("apps.accounts.api.api_views.send_mail")
    @patch("apps.accounts.api.api_views.PasswordResetOTP.generate_otp")
    def test_request_otp_success(self, mock_generate_otp, mock_send_mail):
        mock_otp = MagicMock()
        mock_otp.otp = "123456"
        mock_generate_otp.return_value = mock_otp
        request = self.factory.post(
            "/request-otp/",
            {"email": self.user.email},
        )

        # Attach Django session to APIRequestFactory request
        session = self.client.session
        session.save()
        request.session = session

        response = RequestOtp.as_view()(request)

        self.assertEqual(response.status_code, 200)

        data = response.data

        self.assertTrue(data["success"])
        self.assertIn("message", data)
        self.assertEqual(
            data["redirect_url"],
            "verify-otp/",
        )

        mock_generate_otp.assert_called_once()
        mock_send_mail.assert_called_once()

        # Verify that the email was stored in session
        self.assertEqual(
            request.session.get("reset_email"),
            self.user.email,
        )


    def test_request_otp_invalid_form(self):
        request = self.factory.post(
            "/request-otp/", {"email": "not-an-email"},
        )
        response = RequestOtp.as_view()(request)

        self.assertEqual(response.status_code, 400)
        data = response.data
        self.assertFalse(data["success"])
        self.assertIn("errors", data)

    @patch("apps.accounts.api.api_views.send_mail")
    @patch("apps.accounts.api.api_views.PasswordResetOTP.generate_otp")
    def test_request_otp_nonexistent_email(self, mock_generate_otp, mock_send_mail):
        request = self.factory.post(
            "/request-otp/", {"email": "doesnotexist@test.com",},
        )
        response = RequestOtp.as_view()(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertTrue(data["success"])
        mock_generate_otp.assert_not_called()
        mock_send_mail.assert_not_called()

class VerifyOtpTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="verify_user", email="verify@test.com", password="OldPassword@123",
        )

    def attach_session(self, request, reset_email=None):
        session = self.client.session
        if reset_email is not None:
            session["reset_email"] = reset_email
        session.save()
        request.session = session
        return request

    def test_verify_otp_without_session(self):
        request = self.factory.post(
            "/verify-otp/",
            {"otp": "123456", "new_password": "NewPassword@123"},
        )
        request = self.attach_session(request)
        response = VerifyOtp.as_view()(request)

        self.assertEqual(response.status_code, 400)
        data = response.data
        self.assertFalse(data["success"])
        self.assertEqual(
            data["message"], "Session expired or invalid. Please request a new OTP.",
        )


    def test_verify_otp_missing_fields(self):
        request = self.factory.post(
            "/verify-otp/", {"otp": "", "new_password": ""}
        )

        request = self.attach_session(request, self.user.email)
        response = VerifyOtp.as_view()(request)

        self.assertEqual(response.status_code, 400)
        data = response.data
        self.assertFalse(data["success"])
        self.assertEqual(
            data["message"], "Both OTP and new password are required fields.",
        )

    @patch("apps.accounts.api.api_views.PasswordResetOTP.objects.filter")
    def test_verify_otp_invalid(self, mock_filter):
        mock_filter.return_value.first.return_value = None
        request = self.factory.post(
            "/verify-otp/",
            {"otp": "111111", "new_password": "NewPassword@123"}
        )
        request = self.attach_session(request,  self.user.email)
        response = VerifyOtp.as_view()(request)

        self.assertEqual(response.status_code, 400)
        data = response.data
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Invalid or expired OTP.")

    @patch("apps.accounts.api.api_views.PasswordResetOTP.objects.filter")
    def test_verify_otp_expired(self, mock_filter,):
        mock_otp = MagicMock()
        mock_otp.is_valid.return_value = False
        mock_filter.return_value.first.return_value = mock_otp
        request = self.factory.post(
            "/verify-otp/", {"otp": "111111", "new_password": "NewPassword@123",},
        )
        request = self.attach_session(request, self.user.email)
        response = VerifyOtp.as_view()(request)

        self.assertEqual(response.status_code, 400)
        data = response.data
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Invalid or expired OTP.")

    @patch("apps.accounts.api.api_views.PasswordResetOTP.objects.filter")
    def test_verify_otp_success(self, mock_filter):
        mock_otp = MagicMock()
        mock_otp.is_valid.return_value = True
        mock_filter.return_value.first.return_value = mock_otp
        request = self.factory.post(
            "/verify-otp/",
            {"otp": "123456", "new_password": "NewPassword@123"}
        )
        request = self.attach_session(request, self.user.email)
        response = VerifyOtp.as_view()(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "Password reset successful!")
        self.assertEqual(data["redirect_url"], "login/")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPassword@123"))
        mock_otp.delete.assert_called_once()

    def test_verify_otp_user_does_not_exist(self):
        request = self.factory.post(
            "/verify-otp/", {"otp": "123456", "new_password": "NewPassword@123"}
        )
        request = self.attach_session(request, "missing@test.com")
        response = VerifyOtp.as_view()(request)

        self.assertEqual(response.status_code, 400)
        data = response.data
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "An unexpected identity error occurred.")
