"""
Authentication and profile class based views for the accounts application.

This module contains class based views managing user workflows including registration, 
universal identifier login, password resets via OTP tokens, session management, 
profile modifications, and social follow networks.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from apps.accounts.forms import CustomUserCreationForm, UniversalLoginForm, OTPRequestForm
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from apps.accounts.models import PasswordResetOTP, CustomUser, Contact
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from apps.post.models import SocialPost, Story
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from django.views import View
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from .serializers import CustomUserSerializer, SocialPostSerializer, StorySerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken 

class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        """Process registration data via REST Framework Serializers."""
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({
                "success": True,
                "redirect_url": "/login/"
            }, status=status.HTTP_201_CREATED)
        
        return JsonResponse({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [] 
    def post(self, request):
        form = UniversalLoginForm(request=request, data=request.data)
        if form.is_valid():
            user = form.user_cache
            refresh = RefreshToken.for_user(user)
            return JsonResponse({
                "success": True,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "redirect_url": "/home"
            }, status=status.HTTP_200_OK)
        return JsonResponse({
            "success": False, 
            "errors": form.errors.get_json_data()
        }, status=status.HTTP_400_BAD_REQUEST)


class HomeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        """
        Render central dashboard feed populated with global social post data.
        """
        posts = SocialPost.objects.all() 
        time_threshold = timezone.now() - timedelta(hours=24)
        stories = Story.objects.filter(timestamp__gte=time_threshold).order_by('-timestamp')
        post_serializers = SocialPostSerializer(posts, many=True)
        stories_serializers = SocialPostSerializer(stories, many=True)
        user = request.user.username
        return JsonResponse({"success": True, 'posts': post_serializers.data, 'stories':stories_serializers.data, "User":user}, status=status.HTTP_200_OK)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, username):
        """
        Display public or private account details filtered by specific author.
        """
        if request.user.username != username:
            return redirect('profile_view', username=request.user.username)
        
        posts = SocialPost.objects.filter(author=request.user)
        post_serializers = SocialPostSerializer(posts, many=True)
        return JsonResponse({
            "success": True, 
            'profile_user': request.user.username,
            'posts': post_serializers.data,
        }, status=status.HTTP_200_OK)

class ToggleFollow(APIView):
    """
    Toggle social network graph follow connections asynchronously via JSON.
    """
    permission_classes = [IsAuthenticated]
    def post(self, request):
        target_user_id = request.data.get('id')
        if not target_user_id:
            return JsonResponse({'status': 'error', 'message': 'Missing user ID.'}, status=400)

        target_user = get_object_or_404(CustomUser, id=target_user_id)
        if request.user == target_user:
            return JsonResponse({'status': 'error', 'message': 'You cannot follow yourself.'}, status=400)

        contact, created = Contact.objects.get_or_create(
            user_from=request.user, user_to=target_user
        )
        if created:
            action = 'follow'
        else:
            contact.delete()
            action = 'unfollow'    

        return JsonResponse({'status': 'success',
            'action': action, 'follower_count': target_user.followers.count() 
        })


class EditProfileView(APIView):
    """
    Process custom multi-field user profile changes from direct POST submissions.
    """
    permission_classes = [IsAuthenticated] 
    def post(self, request):
        user = request.user
        user.full_name = request.data.get("full_name", "").strip()
        print(request.data.get("full_name", ""))
        user.bio = request.data.get("bio", "").strip()
        user.website = request.data.get("website", "").strip()
        user.phone_number = request.data.get("phone_number", "").strip()
        user.gender = request.data.get("gender", "")
        dob = request.data.get("date_of_birth")
        if dob:
            user.date_of_birth = dob
        if request.FILES.get("profile_pic"):
            user.profile_pic = request.FILES["profile_pic"]
        user.save()
        return JsonResponse({'success': True, 'username':user.full_name})
