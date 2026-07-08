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
