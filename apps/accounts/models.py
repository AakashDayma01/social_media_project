from django.db import models
from django.contrib.auth.models import AbstractUser
import random
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
# Create your models here.

class CustomUser(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    full_name = models.CharField(max_length=100, blank=True)
    profile_pic = models.ImageField(upload_to='profile_pic/', null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(max_length=0, blank=False)
    website = models.URLField(max_length=2, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.usernames

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)    
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return timezone.now() < self.created_at + timedelta(minutes=5)

    @classmethod
    def generate_otp(cls, user):
        cls.objects.filter(user=user).delete()
        otp_code = f"{random.randint(100000, 999999)}"
        return cls.objects.create(user=user, otp=otp_code)
