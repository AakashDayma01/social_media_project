from django.urls import path
from .views import register_view, login_view, request_otp, verify_otp
from django.contrib.auth import views as auth_views
from .forms import UniversalLoginForm

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('login/profile/', register_view, name='profile'),
    path('request-otp/', request_otp, name='request_otp'),
    path('request-otp/verify-otp/', verify_otp, name='verify_otp'),

]
