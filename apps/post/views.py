from django.shortcuts import render, redirect, get_object_or_404
from .forms import SocialPostForm
from apps.post.models import SocialPost
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Comment
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


def edit_post(request, post_id):
    post = get_object_or_404(SocialPost, id=post_id, author=request.user)
    if request.method == "POST":
        form = SocialPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('home')
        return JsonResponse({"success": False, "errors": form.errors}, status=400)
    else:
        form = SocialPostForm(instance=post)
    return render(request, "posts/edit_post.html", {'form': form, 'post': post})

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

def add_comment(request, post_id):
    post = get_object_or_404(SocialPost, id=post_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        parent = request.POST.get('parent')

        parent_msg = None
        if parent:
            parent_msg = get_object_or_404(Comment, id=parent)
            print(parent)

        comment = Comment.objects.create(post=post, user=request.user, content=content, parent=parent_msg)
        return JsonResponse({
            'success': True,
            'id': comment.id,
            'username': comment.user.username,
            'content': comment.content,
            'parent_id': parent,
            'timestamp': comment.timestamp.strftime('%b %d, %Y %H:%M'),
            'type': 'add'
        })
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def edit_comment(request, post_id):
    post = get_object_or_404(SocialPost, id=post_id)

    if request.method == 'POST':
        parent = request.POST.get('parent')
        comment = get_object_or_404(Comment, id=parent, post=post)

        if comment.user != request.user:
            return JsonResponse({'success': False, 'error': 'You are not allowed to edit this comment.'}, status=403)

        content = request.POST.get('content')
        comment.content = content
        comment.save()
        return JsonResponse({
            'success': True,
            'id': comment.id,
            'username': comment.user.username,
            'content': comment.content,
            'timestamp': comment.timestamp.strftime('%b %d, %Y %H:%M'),
            'type': 'edit'
        })
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
def get_comments(request, post_id):
    post = get_object_or_404(SocialPost, id=post_id)
    all_comments = post.comments.select_related('user').order_by('timestamp')
    comment_tree = {}
    root_comments = []

    for comment in all_comments:
        data = {
            'id': comment.id,
            'username': comment.user.username,
            'content': comment.content,
            'timestamp': comment.timestamp.strftime('%b %d, %Y %H:%M'),
            'replies': [] 
        }
        
        if comment.parent_id is None:
            root_comments.append(data)
        else:
            if comment.parent_id not in comment_tree:
                comment_tree[comment.parent_id] = []
            comment_tree[comment.parent_id].append(data)

    root_comments.reverse()

    def attach_replies(parent_comment):
        parent_id = parent_comment['id']
        if parent_id in comment_tree:
            for reply in comment_tree[parent_id]:
                parent_comment['replies'].append(reply)
                attach_replies(reply)

    for root_comment in root_comments:
        attach_replies(root_comment)
    return JsonResponse({'success': True, 'comments': root_comments})

def delete_comment(request, post_id):
    post = get_object_or_404(SocialPost, id=post_id)

    if request.method == 'POST':
        commentId = request.POST.get('commentId')
        comment = get_object_or_404(Comment, id=commentId, post=post)

        if comment.user != request.user:
            return JsonResponse({'success': False, 'error': 'You are not allowed to delete this comment.'}, status=403)

        comment.delete()
        return JsonResponse({
            'success': True,
            'id': commentId,
            'type': 'delete'
        })
    return JsonResponse({'success': False, 'error': 'Invalid request method'})