from django.urls import path
from .views import register_view, login_view, request_otp, verify_otp, logout_view,home_view
from django.contrib.auth import views as auth_views
from .forms import UniversalLoginForm

urlpatterns = [
    path('home/', home_view, name='home'), 
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('login/profile/', register_view, name='profile'),
    path('request-otp/', request_otp, name='request_otp'),
    path('request-otp/verify-otp/', verify_otp, name='verify_otp'),

]
