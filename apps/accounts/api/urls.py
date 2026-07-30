from django.urls import path
from apps.accounts.api import api_views

urlpatterns = [
    path('register/', api_views.RegisterView.as_view(), name='register'),
    path('login/', api_views.LoginView.as_view(), name='login'),
    path('home/', api_views.HomeView.as_view(), name='home'),
    path('profile/edit/', api_views.EditProfileView.as_view(), name='edit-profile'),
    path('profile/<str:username>/', api_views.ProfileView.as_view(), name='profile_view'),
    path('follow/', api_views.ToggleFollow.as_view(), name='toggle-follow'),
] 