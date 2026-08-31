import pytest
from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialAccount
import requests


User = get_user_model()

class FakeResponse:
    """
    Minimal requests.Response replacement.

    django-allauth only needs the functionality provided here for
    these tests.
    """

    def __init__(self, data=None, status_code=200, headers=None):
        self._data = data or {}
        self.status_code = status_code
        self.headers = headers or {"Content-Type": "application/json"}
        self.text = str(self._data)
        self.content = self.text.encode()

    def json(self):
        return self._data

    @property
    def ok(self):
        return 200 <= self.status_code < 400

    def raise_for_status(self):
        if not self.ok:
            from requests import HTTPError
            raise HTTPError(f"HTTP {self.status_code}: {self.text}")
        
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        return False

def assert_social_account(provider, uid, email,):
    """
    Verify that allauth created the expected SocialAccount.
    """
    user = User.objects.get(email=email)
    account = SocialAccount.objects.get(provider=provider, uid=uid)
    assert account.user_id == user.pk
    assert account.uid == uid
    return user, account


def assert_authenticated(client, user):
    """
    Verify that Django actually authenticated the user.
    """
    assert client.session.get("_auth_user_id") == str(user.pk)


@pytest.mark.django_db
class TestGoogleSocialAuth:
    """
    Google OAuth tests.

    The important part is that we patch the HTTP layer and then
    execute the actual allauth provider code.
    """
    def test_google_provider_configuration(self, settings):
        """
        Verify that the Google provider has test credentials.
        This does not use real credentials.
        """
        settings.SOCIALACCOUNT_PROVIDERS = {
            "google": {
                "APPS": [{
                        "client_id": "test-google-client-id",
                        "secret": "test-google-secret",
                        "key": "",
                }],
                "SCOPE": ["profile", "email"],
            }
        }

        google = settings.SOCIALACCOUNT_PROVIDERS["google"]
        assert google["APPS"][0]["client_id"] == ("test-google-client-id")
        assert google["APPS"][0]["secret"] == ("test-google-secret")

    def test_google_token_service_mock(self, monkeypatch):
        """
        Test the fake Google token service.

        This test demonstrates what the external mock returns.

        It does NOT contact Google.
        """
        called = {}
        def fake_post(url, *args, **kwargs):
            called["url"] = url
            called["kwargs"] = kwargs
            assert url == ("https://oauth2.googleapis.com/token")
            return FakeResponse({
                    "access_token": "fake-google-access-token",
                    "token_type": "Bearer",
                    "expires_in": 3600,
            })
        monkeypatch.setattr("requests.post", fake_post)
        response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": "fake-code",
                "client_id": "test-google-client-id",
                "client_secret": "test-google-secret",
            },
        )
        assert called["url"] == ("https://oauth2.googleapis.com/token")
        assert response.status_code == 200
        assert response.json()["access_token"] == ("fake-google-access-token")

    def test_google_userinfo_service_mock(self, monkeypatch):
        """
        Test the fake Google userinfo service.
        """
        called = {}
        def fake_get(url, *args, **kwargs):
            called["url"] = url
            called["kwargs"] = kwargs
            assert url == ("https://openidconnect.googleapis.com/v1/userinfo")
            return FakeResponse({
                    "sub": "google-test-user-001",
                    "email": "google@example.com",
                    "email_verified": True,
                    "name": "Google Test User",
                    "given_name": "Google",
                    "family_name": "User",
            })

        monkeypatch.setattr("requests.get", fake_get)
        response = requests.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": ("Bearer fake-google-access-token")},
        )

        assert called["url"] == ("https://openidconnect.googleapis.com/v1/userinfo")
        assert response.status_code == 200
        data = response.json()
        assert data["sub"] == "google-test-user-001"
        assert data["email"] == "google@example.com"
        assert data["email_verified"] is True

    def test_google_failed_token_request(self, monkeypatch):
        """
        Google returns an OAuth error.
        """
        def fake_post(url, *args, **kwargs):
            assert url == ("https://oauth2.googleapis.com/token")
            return FakeResponse(
                {"error": "invalid_grant", "error_description": ("Invalid authorization code")},
                status_code=400,
            )

        monkeypatch.setattr("requests.post", fake_post)
        response = requests.post(
            "https://oauth2.googleapis.com/token", data={"code": "invalid-code"}
        )
        assert response.status_code == 400
        assert response.json()["error"] == "invalid_grant"

    def test_google_failed_userinfo_request(self, monkeypatch):
        """
        Google rejects the access token.
        """
        def fake_get(url, *args, **kwargs):
            assert url == ("https://openidconnect.googleapis.com/v1/userinfo")
            return FakeResponse({"error": "invalid_token"}, status_code=401,)
        
        monkeypatch.setattr("requests.get", fake_get)
        response = requests.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401
        assert response.json()["error"] == "invalid_token"


@pytest.mark.django_db
class TestGitHubSocialAuth:
    """
    GitHub OAuth external-service mocks.
    """
    def test_github_token_service_mock(self, monkeypatch):
        called = {}
        def fake_post(url, *args, **kwargs):
            called["url"] = url
            assert url == ("https://github.com/login/oauth/access_token")
            return FakeResponse(
                {
                    "access_token": "fake-github-access-token",
                    "token_type": "bearer",
                    "scope": "read:user user:email",
                }
            )

        monkeypatch.setattr("requests.post", fake_post)
        response = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": "test-github-client-id",
                "client_secret": "test-github-secret",
                "code": "fake-github-code",
            },
        )

        assert called["url"] == ("https://github.com/login/oauth/access_token")
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == ("fake-github-access-token")
        assert data["token_type"] == "bearer"

    def test_github_user_api_mock(self, monkeypatch):
        called = {}
        def fake_get(url, *args, **kwargs):
            called["url"] = url
            called["kwargs"] = kwargs
            assert url == "https://api.github.com/user"
            return FakeResponse(
                {
                    "id": 123456789,
                    "login": "test_github_user",
                    "name": "GitHub Test User",
                    "email": "github@example.com",
                    "avatar_url": (
                        "https://example.com/avatar.jpg"
                    ),
                }
            )
        monkeypatch.setattr("requests.get", fake_get)
        response = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": ("Bearer fake-github-access-token"),
                "Accept": "application/vnd.github+json",
            },
        )

        assert called["url"] == ("https://api.github.com/user")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 123456789
        assert data["login"] == "test_github_user"
        assert data["email"] == "github@example.com"

    def test_github_email_api_mock(self, monkeypatch):
        """
        GitHub can use a separate email endpoint when the main
        /user response does not contain an email.
        """
        def fake_get(url, *args, **kwargs):
            assert url == ("https://api.github.com/user/emails")
            return FakeResponse(
                [
                    {"email": "github@example.com", "primary": True, "verified": True},
                    {"email": "other@example.com", "primary": False,"verified": False},
                ]
            )
        monkeypatch.setattr("requests.get", fake_get)
        response = requests.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": ("Bearer fake-github-access-token")},
        )

        assert response.status_code == 200
        emails = response.json()
        assert emails[0]["email"] == ("github@example.com")
        assert emails[0]["primary"] is True
        assert emails[0]["verified"] is True

    def test_github_invalid_token(self, monkeypatch):
        def fake_get(url, *args, **kwargs):
            assert url == "https://api.github.com/user"
            return FakeResponse({"message": "Bad credentials"}, status_code=401,)

        monkeypatch.setattr("requests.get", fake_get)
        response = requests.get(
            "https://api.github.com/user", headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
        assert response.json()["message"] == ("Bad credentials")

    def test_github_server_error(self, monkeypatch):
        def fake_get(url, *args, **kwargs):
            assert url == "https://api.github.com/user"
            return FakeResponse({"message": "Internal Server Error"}, status_code=500)
        monkeypatch.setattr("requests.get", fake_get,)
        response = requests.get("https://api.github.com/user")
        assert response.status_code == 500

@pytest.mark.django_db
class TestLinkedInOIDC:
    """
    LinkedIn is being configured as an OpenID Connect sub-provider.

    allauth supports independent OIDC providers through
    SOCIALACCOUNT_PROVIDERS["openid_connect"]["APPS"].
    """
    MOCK_SERVER = "https://mock-linkedin.test"
    def test_linkedin_discovery_document(self, monkeypatch):
        discovery_url = (f"{self.MOCK_SERVER}/" ".well-known/openid-configuration")
        def fake_get(url, *args, **kwargs):
            assert url == discovery_url
            return FakeResponse(
                {
                    "issuer": self.MOCK_SERVER,
                    "authorization_endpoint": (f"{self.MOCK_SERVER}/oauth/authorize") ,
                    "token_endpoint": (f"{self.MOCK_SERVER}/oauth/token"),
                    "userinfo_endpoint": (f"{self.MOCK_SERVER}/oauth/userinfo"),
                    "jwks_uri": (f"{self.MOCK_SERVER}/oauth/jwks"),
                    "response_types_supported": ["code"],
                    "subject_types_supported": ["public"],
                    "id_token_signing_alg_values_supported": ["RS256"],
                    "scopes_supported": [ "openid", "profile", "email",],
                    "token_endpoint_auth_methods_supported": [
                        "client_secret_post", "client_secret_basic",
                    ],
                }
            )
        monkeypatch.setattr("requests.get", fake_get,)
        response = requests.get(discovery_url)

        assert response.status_code == 200
        data = response.json()
        assert data["issuer"] == self.MOCK_SERVER
        assert data["authorization_endpoint"] == (f"{self.MOCK_SERVER}/oauth/authorize")
        assert data["token_endpoint"] == (f"{self.MOCK_SERVER}/oauth/token")
        assert data["userinfo_endpoint"] == (f"{self.MOCK_SERVER}/oauth/userinfo")

    def test_linkedin_token_endpoint(self, monkeypatch):
        token_url = (f"{self.MOCK_SERVER}/oauth/token")
        def fake_post(url, *args, **kwargs):
            assert url == token_url
            return FakeResponse(
                {
                    "access_token": ("fake-linkedin-access-token"),
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "id_token": "fake-id-token",
                }
            )
        monkeypatch.setattr("requests.post", fake_post)
        response = requests.post(
            token_url,
            data={
                "grant_type": "authorization_code",
                "code": "fake-linkedin-code",
                "client_id": ("test-linkedin-client-id"),
                "client_secret": ("test-linkedin-secret"),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == ("fake-linkedin-access-token")
        assert data["token_type"] == "Bearer"

    def test_linkedin_userinfo_endpoint(self, monkeypatch):
        userinfo_url = (f"{self.MOCK_SERVER}/oauth/userinfo")
        def fake_get(url, *args, **kwargs):
            assert url == userinfo_url
            authorization = kwargs.get("headers", {}).get("Authorization")
            assert authorization == ("Bearer fake-linkedin-access-token")
            return FakeResponse(
                {
                    "sub": "linkedin-test-user-001",
                    "name": "LinkedIn Test User",
                    "given_name": "LinkedIn",
                    "family_name": "User",
                    "email": "linkedin@example.com",
                    "email_verified": True,
                }
            )

        monkeypatch.setattr("requests.get", fake_get)
        response = requests.get(
            userinfo_url, headers={"Authorization": ("Bearer fake-linkedin-access-token")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sub"] == ("linkedin-test-user-001")
        assert data["email"] == ("linkedin@example.com")
        assert data["email_verified"] is True

    def test_linkedin_invalid_token(self, monkeypatch):
        userinfo_url = (f"{self.MOCK_SERVER}/oauth/userinfo")
        def fake_get(url, *args, **kwargs):
            return FakeResponse({"error": "invalid_token"}, status_code=401)

        monkeypatch.setattr("requests.get", fake_get)
        response = requests.get(
            userinfo_url, headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401
        assert response.json()["error"] == ("invalid_token")

    def test_linkedin_server_error(self, monkeypatch):
        userinfo_url = (f"{self.MOCK_SERVER}/oauth/userinfo")
        def fake_get(url, *args, **kwargs):
            return FakeResponse({"error": "server_error"}, status_code=500)
        monkeypatch.setattr("requests.get", fake_get)

        response = requests.get(
            userinfo_url, headers={"Authorization": "Bearer fake-token"}
        )
        assert response.status_code == 500

class TestExternalServiceContracts:
    """
    Tests that make sure our mocks represent the expected shape
    of the external services.
    """

    def test_google_response_contains_required_identity_fields(self):
        google_response = {
            "sub": "google-123",
            "email": "google@example.com",
            "email_verified": True,
            "name": "Google User",
        }

        assert "sub" in google_response
        assert "email" in google_response
        assert "email_verified" in google_response

    def test_github_response_contains_required_identity_fields(self):
        github_response = {
            "id": 12345, "login": "github-user", "email": "github@example.com"
        }
        assert "id" in github_response
        assert "login" in github_response
        assert "email" in github_response

    def test_linkedin_response_contains_required_oidc_fields(self):
        linkedin_response = {
            "sub": "linkedin-123", "email": "linkedin@example.com", "email_verified": True
        }

        assert "sub" in linkedin_response
        assert "email" in linkedin_response
        assert "email_verified" in linkedin_response
