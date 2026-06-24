from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm

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

