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

urlpatterns = [
    path('home/', views.home_view, name='home'), 
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('request-otp/', views.request_otp, name='request_otp'),
    path('request-otp/verify-otp/', views.verify_otp, name='verify_otp'),
    path('user/toggle-follow/', views.toggle_follow, name='toggle_follow'),
    path("profile/edit/", views.edit_profile_view, name="edit_profile"),
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
]
