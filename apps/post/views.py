from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import SocialPostForm
from apps.post.models import SocialPost
from django.contrib import messages

# Create your views here.

@login_required
def create_post(request):
    if request.method == 'POST':
        form = SocialPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('home')  
    else:
        form = SocialPostForm()
        
    return render(request, 'posts/create_post.html', {'form': form})

@login_required
def like_post(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(SocialPost, id=post_id)
        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
        else:
            post.likes.add(request.user)
    return redirect('home')


@login_required
def delete_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(SocialPost, id=post_id)
        if post.author == request.user:
            post.delete()
    return redirect('home')
