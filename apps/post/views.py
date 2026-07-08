from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import SocialPostForm
from apps.post.models import SocialPost
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
# Create your views here.

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

@extend_schema(
    summary="Like or unlike a post",
    responses={
        200: OpenApiResponse(description="Success returns like status and total count."),
        403: OpenApiResponse(description="CSRF Token missing or invalid.")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_post(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(SocialPost, id=post_id)
        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
        return JsonResponse({"success": True, "liked": liked, "total_likes": post.likes.count()})
    return JsonResponse({"success": False}, status=400)

@login_required
def delete_post(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(SocialPost, id=post_id)
        if post.author == request.user:
            post.delete()
            return JsonResponse({"success": True})
        return JsonResponse({"success": False,
            "message": "You are not allowed to delete this post."
        }, status=403)
    return JsonResponse({"success": False}, status=400)

