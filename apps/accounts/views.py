from django.shortcuts import render, redirect
from django.http import JsonResponse

# Create your views here.
from django.shortcuts import render
from .forms import CustomUserCreationForm
from django.contrib.auth import authenticate, login
from django.conf import settings
from .forms import UniversalLoginForm


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
                        'redirect_url': settings.LOGIN_REDIRECT_URL
                    })
                return redirect(settings.LOGIN_REDIRECT_URL)

            else:
                form.add_error(None, "Invalid credentials. Please verify your entries.")
        else:
            return JsonResponse({'success': False, 'errors': form.errors.get_json_data()}, status=400)   

    else:
        form = UniversalLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


