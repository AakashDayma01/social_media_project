from rest_framework import serializers
from apps.accounts.models import CustomUser, Contact, PasswordResetOTP
from apps.post.models import SocialPost, Story

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = "__all__"

class SocialPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialPost
        fields = "__all__"

class StorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = "__all__"