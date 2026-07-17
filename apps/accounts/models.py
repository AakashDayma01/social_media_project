"""
Database models for the accounts application.
This module defines the schema and business logic for user profiles, 
social relationships (followers/following), and security tokens.

Models:
    CustomUser: Extended user profile containing personal demographics and social links.
    Contact: Intermediary asymmetric tracking model for user-to-user follow statuses.
    PasswordResetOTP: Security model managing expiration and issuance of 6-digit tokens.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
import random
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
# Create your models here.

class CustomUser(AbstractUser):
    """
    Custom user model expanding the default Django user behavior.
    Adds support for profile customization, social metrics (following/followers),
    and additional personal identification fields like phone numbers.
    """
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    full_name = models.CharField(max_length=100, blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(max_length=150, blank=True)
    website = models.URLField(blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    following = models.ManyToManyField(
        'self', through='Contact', related_name='followers', symmetrical=False
    )
    def __str__(self):
        """
        Returns the string representation of the user.
        """
        return self.username
    

class Contact(models.Model):
    """
    Intermediary M2M model representing follow relationships between users.
    """
    user_from = models.ForeignKey(settings.AUTH_USER_MODEL, 
        related_name='rel_from_set', on_delete=models.CASCADE
    )
    user_to = models.ForeignKey(settings.AUTH_USER_MODEL, 
        related_name='rel_to_set', on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ('-created',)
        constraints = [
            models.UniqueConstraint(fields=['user_from', 'user_to'], name='unique_followers')
        ]

    def __str__(self):
        """
        Returns the directional relationship description string.
        """
        return f'{self.user_from} follows {self.user_to}'



class PasswordResetOTP(models.Model):
    """
    Stores temporary short-lived OTP tokens used for account verification.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)    
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        """
        Checks if the generated OTP token is less than 5 minutes old.
        Returns:
            bool: True if the token has not expired yet, False otherwise.
        """
        return timezone.now() < self.created_at + timedelta(minutes=5)

    @classmethod
    def generate_otp(cls, user):
        """
        Invalidates existing user tokens and issues a new random 6-digit OTP.
        Args: user (CustomUser): The user requesting a token refresh.
        Returns: PasswordResetOTP: The newly saved database token instance.
        """
        cls.objects.filter(user=user).delete()
        otp_code = f"{random.randint(100000, 999999)}"
        return cls.objects.create(user=user, otp=otp_code)
    


