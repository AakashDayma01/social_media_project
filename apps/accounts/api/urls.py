from django.urls import path
from apps.accounts.api import api_views

urlpatterns = [
    path('register/', api_views.RegisterView.as_view(), name='register'),
    path('login/', api_views.LoginView.as_view(), name='login'),
    path('home/', api_views.HomeView.as_view(), name='home'),
    path('profile/edit/<int:user_id>/', api_views.EditProfileView.as_view(), name='edit-profile'),
    path('profile/<str:username>/', api_views.ProfileView.as_view(), name='profile_view'),
    path('follow/', api_views.ToggleFollow.as_view(), name='toggle-follow'),
    path('logout/',api_views.LogoutAPIView.as_view(), name="logout"),
    path('request-otp/',api_views.RequestOtp.as_view(), name="request-otp"),
    path('verify-otp/',api_views.VerifyOtp.as_view(), name="verify-otp")
]
