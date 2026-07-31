"""
Authentication and profile class based views for the accounts application.

This module contains class based views managing user workflows including registration, 
universal identifier login, password resets via OTP tokens, session management, 
profile modifications, and social follow networks.
"""
from django.core.mail import send_mail
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from apps.accounts.forms import OTPRequestForm, UniversalLoginForm
from django.contrib.auth import get_user_model
from django.conf import settings
from apps.accounts.models import CustomUser, Contact, PasswordResetOTP, CustomUser
from django.contrib.auth import logout
from apps.post.models import SocialPost, Story
from django.utils import timezone
from datetime import timedelta
from .serializers import CustomUserSerializer, SocialPostSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken 
from rest_framework.response import Response


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
    def post(self, request, user_id):
        target_user = get_object_or_404(CustomUser, pk=user_id)
        if request.user != target_user:
            return Response(
                {"detail": "You do not have permission to edit this profile."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        user = request.user
        user.full_name = request.data.get("full_name", "").strip()
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

class LogoutAPIView(APIView):
    """
    Blacklists the active JWT refresh token and clears Django sessions.
    """
    permission_classes = [IsAuthenticated]
    def post(self, request):
        logout(request)
        
        response = Response(
            {"detail": "Successfully logged out on server."}, 
            status=status.HTTP_200_OK
        )
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response

class RequestOtp(APIView):
    """
    Validate target user emails and distribute short-lived OTP tokens via SMTP.
    Persists targeted credentials to the current user tracking session.
    """
    User = get_user_model()
    permission_classes = [AllowAny]
    def post(self, request):
        form = OTPRequestForm(request.POST)
        if not form.is_valid():
            return Response({
                'success': False, 
                'errors': form.errors.get_json_data() if hasattr(form.errors, 'get_json_data') else form.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        email = form.cleaned_data['email'].strip()
        user = self.User.objects.filter(email__iexact=email).first()
        if user is not None:
            otp_obj = PasswordResetOTP.generate_otp(user)
            send_mail(
                'Your Pasjsword Reset OTP',
                f'Your OTP code is {otp_obj.otp}. It expires in 5 minutes.',
                settings.DEFAULT_FROM_EMAIL, 
                [email],
                fail_silently=False,
            )
            request.session['reset_email'] = email

        return Response({
            'success': True, 
            'message': 'If a matching account exists, an OTP has been sent successfully.',
            'redirect_url': 'verify-otp/'
        }, status=status.HTTP_200_OK)

class VerifyOtp(APIView):
    """
    Verify incoming user-supplied safety tokens against database OTP instances.
    Updates system passwords securely and flushes reset keys from active sessions.
    """
    User = get_user_model()
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.session.get('reset_email')
        if not email:
            return Response({
                "success": False,
                "message": "Session expired or invalid. Please request a new OTP.",
                "redirect_url": "request-otp/"
            }, status=status.HTTP_400_BAD_REQUEST)
        otp_entered = request.data.get('otp')
        new_password = request.data.get('new_password')
        if not otp_entered or not new_password:
            return Response({
                "success": False,
                "message": "Both OTP and new password are required fields."
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = self.User.objects.get(email=email)
            otp_record = PasswordResetOTP.objects.filter(
                user=user,
                otp=otp_entered
            ).first()
            if otp_record and otp_record.is_valid():
                user.set_password(new_password)
                user.save()
                otp_record.delete()
                if 'reset_email' in request.session:
                    del request.session['reset_email']

                return Response({
                    "success": True,
                    "message": "Password reset successful!",
                    "redirect_url": "login/"
                }, status=status.HTTP_200_OK)
            return Response({
                "success": False,
                "message": "Invalid or expired OTP."
            }, status=status.HTTP_400_BAD_REQUEST)

        except self.User.DoesNotExist:
            return Response({
                "success": False,
                "message": "An unexpected identity error occurred."
            }, status=status.HTTP_400_BAD_REQUEST)