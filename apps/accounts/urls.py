"""
URL configuration for the accounts application.

This module maps incoming HTTP request routes to their corresponding view functions 
handling user sessions, profile management, OTP verification, and social interactions.

Routes:
    - home/ : Core user dashboard or feed landing page.
    - logout/ : Terminates user authentication sessions.
    - register/ : Renders and processes account creation forms.
    - login/ : Processes user authentication credentials.
    - request-otp/ : Handles verification token generation requests.
    - request-otp/verify-otp/ : Direct target for evaluating user-submitted tokens.
    - user/toggle-follow/ : API or view endpoint to follow/unfollow accounts.
    - profile/edit/ : Interface for updating personal user profile details.
    - profile/<username>/ : Dynamic routing to display a specific user's public page.
"""
from django.urls import path
from . import views
from . import class_view

urlpatterns = [
    path('home/', class_view.HomeView.as_view(), name='home'), 
    path('logout/', class_view.LogoutView.as_view(), name='logout'),
    path('register/', class_view.RegisterView.as_view(), name='register'),
    path('login/', class_view.LoginVIew.as_view(), name='login'),
    path('request-otp/', class_view.RequestOtp.as_view(), name='request_otp'),
    path('request-otp/verify-otp/', class_view.VerifyOtp.as_view(), name='verify_otp'),
    path('user/toggle-follow/', class_view.ToggleFollow.as_view(), name='toggle_follow'),
    path("profile/edit/", class_view.EditProfileView.as_view(), name="edit_profile"),
    path('profile/<str:username>/', class_view.ProfileView.as_view(), name='profile_view'),
]
