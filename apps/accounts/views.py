from django.shortcuts import render, redirect
from django.http import JsonResponse

# Create your views here.
from django.shortcuts import render
from .forms import CustomUserCreationForm
from django.contrib.auth import authenticate, login
from django.conf import settings
from .forms import UniversalLoginForm, OTPRequestForm

from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from .models import PasswordResetOTP 

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
      #  return redirect(settings.LOGIN_REDIRECT_URL)

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
                        'redirect_url': 'profile/'
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
