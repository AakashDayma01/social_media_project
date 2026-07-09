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
from django.contrib.auth.decorators import login_required
from apps.post.models import SocialPost
from .models import CustomUser, Contact
from django.views.decorators.http import require_POST


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'redirect_url': '/login/'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors.get_json_data()}, status=400)   
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'accounts/registration.html', {'form': form})

def login_view(request):
    #if request.user.is_authenticated:
      #a  return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == 'POST':
        form = UniversalLoginForm(data=request.POST)
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
    else:
        form = UniversalLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def request_otp(request):
    User = get_user_model()
    
    if request.method == 'POST':
        form = OTPRequestForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email'].strip()
            user = User.objects.filter(email__iexact=email).first()
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

    else:
        form = OTPRequestForm()

    return render(request, 'accounts/request_otp.html', {'form': form})


def verify_otp(request):
    User = get_user_model()
    email = request.session.get('reset_email')
    if not email:
        return redirect('accounts/request_otp')

    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        
        try:
            user = User.objects.get(email=email)
            otp_record = PasswordResetOTP.objects.filter(user=user, otp=otp_entered).first()
            
            if otp_record and otp_record.is_valid():
                user.set_password(new_password)
                user.save()
                otp_record.delete()
                del request.session['reset_email']
                messages.success(request, "Password reset successful!")
                return redirect('login') 
            else:
                messages.error(request, "Invalid or expired OTP.")
        except User.DoesNotExist:
            messages.error(request, "An error occurred.")
            
    return render(request, 'accounts/verify_otp.html')


def logout_view(request):
    """
    Clears the session cookies and logs the user out entirely from 
    Django and allauth social providers.
    """
    logout(request)
    return redirect('login') 

@login_required
def home_view(request):
    posts = SocialPost.objects.all() 
    return render(request, 'home.html', {'posts': posts})


@login_required
def profile_view(request, username):
    if request.user.username != username:
        return redirect('profile_view', username=request.user.username)
    
    posts = SocialPost.objects.filter(author=request.user)
    
    return render(request, 'accounts/profile.html', {
        'profile_user': request.user,
        'posts': posts,
    })
    
def edit_profile_view(request):
    user = request.user

    if request.method == "POST":
        user.full_name = request.POST.get("full_name", "").strip()
        user.bio = request.POST.get("bio", "").strip()
        user.website = request.POST.get("website", "").strip()
        user.phone_number = request.POST.get("phone_number", "").strip()
        user.gender = request.POST.get("gender", "")
        dob = request.POST.get("date_of_birth")
        if dob:
            user.date_of_birth = dob
        if request.FILES.get("profile_pic"):
            user.profile_pic = request.FILES["profile_pic"]
        user.save()
        return redirect("profile_view", username=user.username)

    return render(request, "accounts/edit_profile.html")

@require_POST 
def toggle_follow(request):
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
