from django.urls import path
from .views import register_view, login_view
from django.contrib.auth import views as auth_views
from .forms import UniversalLoginForm

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('login/profile', register_view, name='profile')
]
