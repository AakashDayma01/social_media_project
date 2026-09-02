"""
Authentication and profile class based views for the accounts application.

This module contains class based views managing user workflows including registration,
universal identifier login, password resets via OTP tokens, session management,
profile modifications, and social follow networks.
"""
import re

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .forms import CustomUserCreationForm
from django.contrib.auth import authenticate, login
from django.conf import settings
from .forms import UniversalLoginForm, OTPRequestForm
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from .models import PasswordResetOTP
from django.contrib.auth import logout
from apps.post.models import SocialPost, Story
from .models import CustomUser, Contact
from django.utils import timezone
from datetime import date, timedelta
from django.views import View
from django.urls import reverse
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
import stripe

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator



stripe.api_key = settings.STRIPE_SECRET_KEY

class RegisterView(View):
    """
    Handle user registration and process account creation forms.

    Accepts standard browser requests as well as structured AJAX POST elements.
    Returns JSON response strings containing routing context when successful.
    """
    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, 'accounts/registration.html', {'form': form})

    def post(self, request):
        if request.method == 'POST':
            form = CustomUserCreationForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                return JsonResponse({'success': True, 'redirect_url': '/login/'})
            else:
                return JsonResponse({'success': False, 'errors': form.errors.get_json_data()}, status=400)

class LoginVIew(View):
    """
    Authenticate users utilizing a multi-identifier universal login form.

    Populates standard session structures or transmits payload data objects
    back to asynchronous frontend fetch/XMLHttpRequest handlers.
    """
    #if request.user.is_authenticated:
      #a  return redirect(settings.LOGIN_REDIRECT_URL)
    def get(self, request):
        form = UniversalLoginForm()
        return render(request, 'accounts/login.html', {'form': form})
    def post(self, request):
        if request.method == 'POST':
            form = UniversalLoginForm(request=request,data=request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'redirect_url': '/home'
                        })
                    return redirect(settings.LOGIN_REDIRECT_URL)
                else:
                    form.add_error(None, "Invalid credentials. Please verify your entries.")
            else:
                return JsonResponse({'success': False, 'errors': form.errors.get_json_data()}, status=400)



class RequestOtp(View):
    """
    Validate target user emails and distribute short-lived OTP tokens via SMTP.
    Persists targeted credentials to the current user tracking session.
    """
    User = get_user_model()
    def get(self, request):
        form = OTPRequestForm()
        return render(request, 'accounts/request_otp.html', {'form': form})

    def post(self, request):
        if request.method == 'POST':
            form = OTPRequestForm(request.POST)

            if form.is_valid():
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
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'redirect_url': 'verify-otp/'
                        })
                    return redirect(settings.LOGIN_REDIRECT_URL)

                else:
                    form.add_error('email', 'No user found with this email.')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors.get_json_data()
                }, status=400)

class VerifyOtp(View):
    """
    Verify incoming user-supplied safety tokens against database OTP instances.
    Updates system passwords securely and flushes reset keys from active sessions.
    """
    User = get_user_model()
    def get(self, request):
        return render(request, 'accounts/verify_otp.html')
    def post(self, request):
        email = request.session.get('reset_email')
        if not email:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": False,
                    "message": "Session expired. Please request a new OTP."
                }, status=400)
            return redirect('request_otp')
        if request.method == 'POST':
            otp_entered = request.POST.get('otp')
            new_password = request.POST.get('new_password')
            print("otp", otp_entered)

            try:
                user = self.User.objects.get(email=email)
                otp_record = PasswordResetOTP.objects.filter(
                    user=user, otp=otp_entered
                ).first()

                if otp_record and otp_record.is_valid():
                    user.set_password(new_password)
                    user.save()
                    otp_record.delete()
                    del request.session['reset_email']

                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            "success": True,
                            "redirect_url": reverse("login")
                        })

                    messages.success(request, "Password reset successful!")
                    return redirect("login")

                else:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            "success": False,
                            "message": "Invalid or expired OTP."
                        }, status=400)

                    messages.error(request, "Invalid or expired OTP.")

            except self.User.DoesNotExist:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        "success": False,
                        "message": "An error occurred."
                    }, status=400)

                messages.error(request, "An error occurred.")


class LogoutView(View):
    """
    Clears the session cookies and logs the user out entirely from
    Django and allauth social providers.
    """
    def post(self, request):
        logout(request)
        return redirect('login')


class HomeView(LoginRequiredMixin, View):
    def get(self, request):
        """
        Render central dashboard feed populated with global social post data.
        """
        posts_list = SocialPost.objects.all().order_by('-id')
        paginator = Paginator(posts_list, 2)
        page_number = request.GET.get('page')
        posts_page = paginator.get_page(page_number)
        time_threshold = timezone.now() - timedelta(hours=24)
        stories = Story.objects.filter(timestamp__gte=time_threshold).order_by('-timestamp')
        return render(request, 'home.html', {'posts': posts_page, 'stories': stories})

class ProfileView(LoginRequiredMixin, View):
    def get(self, request, username):
        """
        Display public or private account details filtered by specific author.
        """
        if request.user.username != username:
            return redirect('profile_view', username=request.user.username)
        posts = SocialPost.objects.filter(author=request.user)

        return render(request, 'accounts/profile.html', {
            'profile_user': request.user,
            'posts': posts,
        })


class EditProfileView(View):
    """
    Process custom multi-field user profile changes from direct POST submissions.
    """
    def get(self, request):
        return render(request, "accounts/edit_profile.html")
    
    def post(self, request):
        user = request.user
        errors = {}
        full_name = request.POST.get("full_name", "").strip()
        if not full_name:
            errors["full_name"] = "Please enter your full name."
        elif not re.fullmatch(r"[A-Za-z ]+", full_name):
            errors["full_name"] = "Full name can contain only letters and spaces."
        phone_number = request.POST.get("phone_number", "").strip()
        if not re.fullmatch(r"[6-9]\d{9}", phone_number):
            errors["phone_number"] = "Enter a valid 10-digit mobile number."
        gender = request.POST.get("gender", "").strip()
        if gender not in ["Male", "Female", "Other"]:
            errors["gender"] = "Please select a valid gender."
        dob = request.POST.get("date_of_birth", "").strip()
        if dob:
            try:
                dob = date.fromisoformat(dob)
                today = date.today()
                age = (
                    today.year - dob.year
                    - ((today.month, today.day) < (dob.month, dob.day))
                )
                if age < 12:
                    errors["date_of_birth"] = ("You must be at least 12 years old.")
            except ValueError:
                errors["date_of_birth"] = "Enter a valid date of birth."
        profile_pic = request.FILES.get("profile_pic")

        if profile_pic:
            if profile_pic.content_type not in ["image/jpeg","image/png","image/webp",]:
                errors["profile_pic"] = (
                    "Only JPG, PNG and WEBP images are allowed."
                )
        if errors:
            return JsonResponse(
                {"success": False, "errors": errors}, status=400,
            )
        user.full_name = full_name
        user.bio = request.POST.get("bio", "").strip()
        user.website = request.POST.get("website", "").strip()
        user.phone_number = phone_number
        user.gender = gender

        if dob:
            user.date_of_birth = dob
        if profile_pic:
            user.profile_pic = profile_pic
        user.save()
        return JsonResponse(
            {
                "success": True,
                "message": "Profile updated successfully.",
                "redirect_url": redirect(
                    "profile_view",
                    username=user.username
                ).url,
            }
        )

class ToggleFollow(View):
    """
    Toggle social network graph follow connections asynchronously via JSON.
    """
    def post(self, request):
        target_user_id = request.POST.get('id')
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


class CreateVerificationCheckoutView(LoginRequiredMixin, View):
    """
    Create a Stripe Checkout Session for account verification.
    """
    def post(self, request):
        if request.user.is_verified:
            return JsonResponse({
                "success": False, "message": "Your account is already verified."
            }, status=400)
        try:
            checkout_session = stripe.checkout.Session.create(
                mode="payment",
                line_items=[
                    {
                        "price_data": {
                            "currency": "inr",
                            "product_data": {
                                "name": "Verified Account",
                                "description": "Social media account verification",
                            },
                            "unit_amount": 49900,
                        },
                        "quantity": 1,
                    }
                ],
                metadata={"user_id": str(request.user.id),},
                success_url=request.build_absolute_uri(
                    reverse("profile_view", kwargs={"username": request.user.username})
                ) + "?verification=success",
                cancel_url=request.build_absolute_uri(
                    reverse("profile_view", kwargs={"username": request.user.username})
                ) + "?verification=cancelled",
            )
            return redirect(checkout_session.url)
        except stripe.error.StripeError as e:
            return JsonResponse({"success": False, "message": str(e),}, status=400)
        except Exception:
            return JsonResponse({
                "success": False, "message": "Something went wrong.",
            }, status=500)

@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET,
            )
        except ValueError as e:
            return JsonResponse(
                {"error": "Invalid payload"}, status=400,
            )
        except stripe.error.SignatureVerificationError as e:
            return JsonResponse(
                {"error": "Invalid signature"},
                status=400,
            )
        if event["type"] == "checkout.session.completed":
            try:
                session = event["data"]["object"]
                metadata = session.metadata
                user_id = metadata["user_id"]
                if not user_id:
                    return JsonResponse(
                        {"error": "User ID missing from metadata"}, status=400,
                    )
                user = CustomUser.objects.get(id=int(user_id))
                if not user.is_verified:
                    user.is_verified = True
                    user.save(update_fields=["is_verified"])
            except Exception as e:
                return JsonResponse(
                    { "error": "Webhook processing failed", "details": str(e)}, status=500,
                )
        return JsonResponse({"status": "success"})