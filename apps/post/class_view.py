"""
Business logic and request controllers for the post application.

This module exposes functional endpoints managing standard database operations (CRUD)
for media-supported social updates, fully asynchronous nested conversational commenting hierarchies,
interaction metrics (likes), and system notifications.
"""
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from .forms import SocialPostForm, StoryForm
from apps.post.models import SocialPost, Story
from django.http import JsonResponse
from .models import Comment
from django.utils import timezone
from django.views import View
# Create your views here.

class CreatePost(View):
    """
    Render or process the submission form for publishing a new entry.
    Binds the incoming upload assets and text values directly to the active session user.
    """
    def get(self, request):
        form = SocialPostForm()     
        return render(request, 'posts/create_post.html', {'form': form})
    def post(self, request):
        if request.method == 'POST':
            form = SocialPostForm(request.POST, request.FILES)
            if form.is_valid():
                post = form.save(commit=False)
                post.author = request.user
                post.save()
                return redirect('home')  


class EditPost(View):
    """
    Modify an existing publication instance owned by the current user.
    Returns structured error JSON components if an unexpected form validation gap occurs.
    """
    def get(self, request,post_id):
        post = get_object_or_404(SocialPost, id=post_id, author=request.user)
        form = SocialPostForm(instance=post)
        return render(request, "posts/edit_post.html", {'form': form, 'post': post})
        
    def post(self, request, post_id):
        post = get_object_or_404(SocialPost, id=post_id, author=request.user)
        if request.method == "POST":
            form = SocialPostForm(request.POST, request.FILES, instance=post)
            if form.is_valid():
                form.save()
                return redirect('home')
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

class LikePost(View):
    """
    Toggle a user's recommendation preference status for a particular post.
    Calculates aggregate metrics and returns boolean operations tracking interaction changes.
    """
    def get(self, request):
        return JsonResponse({"success": False}, status=400)
    def post(self, request, post_id):
        if request.method == "POST":
            post = get_object_or_404(SocialPost, id=post_id)
            if post.likes.filter(id=request.user.id).exists():
                post.likes.remove(request.user)
                liked = False
            else:
                post.likes.add(request.user)
                liked = True
            return JsonResponse({"success": True, 
                "liked": liked,
                "total_likes": post.likes.count()
            })

class DeletePost(View):
    """
    Hard-remove a specific publication entry entirely from the database.
    Enforces ownership criteria validation prior to conducting the deletion step.
    """
    def get(self, request):
        return JsonResponse({"success": False}, status=400)
    def post(self, request, post_id):
        if request.method == "POST":
            post = get_object_or_404(SocialPost, id=post_id)
            if post.author == request.user:
                post.delete()
                return JsonResponse({"success": True})
            return JsonResponse({"success": False,
                "message": "You are not allowed to delete this post."
            }, status=403)

class AddComment(View):
    """
    Publish a flat top-level remark or a deeply nested sub-conversational response.
    """
    def get(self, request):
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    def post(self, request, post_id):
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
                'liked_by_user': request.user in comment.likes.all(),
                'total_likes': comment.likes.count(),
                'type': 'add'
            })


class EditComments(View):
    """
    Update text components of an existing user-authored conversation entry.
    """
    def get(self, request):
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    def post(self, request, post_id):
        post = get_object_or_404(SocialPost, id=post_id)
        if request.method == 'POST':
            parent = request.POST.get('parent')
            comment = get_object_or_404(Comment, id=parent, post=post)

            if comment.user != request.user:
                return JsonResponse({'success': False, 
                    'error': 'You are not allowed to edit this comment.'
                }, status=403)

            content = request.POST.get('content')
            comment.content = content
            comment.timestamp = timezone.now() 
            comment.save()
            return JsonResponse({
                'success': True,
                'id': comment.id,
                'username': comment.user.username,
                'content': comment.content,
                'timestamp': comment.timestamp.strftime('%b %d, %Y %H:%M'),
                'liked_by_user': request.user in comment.likes.all(),
                'total_likes': comment.likes.count(),
                'type': 'edit'
            })

class GetComments(View):
    """
    Retrieve and construct an algorithmic nested tree of message data components.
    """     
    def get(self, request, post_id):
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
                'liked_by_user': request.user in comment.likes.all(),
                'total_likes': comment.likes.count(),
                'is_deleted': comment.is_deleted,
                'replies': [] 
            }
            
            if comment.parent_id is None:
                root_comments.append(data)
            else:
                if comment.parent_id not in comment_tree:
                    comment_tree[comment.parent_id] = []
                comment_tree[comment.parent_id].append(data)
    
        def attach_replies(parent_comment):
            parent_id = parent_comment['id']
            if parent_id in comment_tree:
                for reply in comment_tree[parent_id]:
                    parent_comment['replies'].append(reply)
                    attach_replies(reply)
    
        for root_comment in root_comments:
            attach_replies(root_comment)
        return JsonResponse({'success': True, 'comments': root_comments})

class DeleteComment(View):
    """
    Flag a comment entry as deleted and securely wipe text and interaction contents.
    """
    def add(self, request):
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    def post(self, request, post_id):
        post = get_object_or_404(SocialPost, id=post_id)

        if request.method == 'POST':
            comment_id = request.POST.get('comment_id')
            comment = get_object_or_404(Comment, id=comment_id, post=post)

            if comment.user != request.user:
                return JsonResponse({'success': False, 
                    'error': 'You are not allowed to delete this comment.'
                }, status=403)

            comment.content = 'This comment has been deleted.'
            comment.is_deleted = True
            comment.likes.clear()
            comment.timestamp = timezone.now()
            comment.save()
            return JsonResponse({
                'success': True,
                'id': comment_id,
                'content': comment.content,
                'is_deleted': comment.is_deleted,
                'timestamp': comment.timestamp.strftime('%b %d, %Y %H:%M'),
                'type': 'delete'
            })
    
class LikeComment(View):
    """
    Toggle a user's recommendation metrics for an individual conversation row.
    """
    def get(self, request):
        return JsonResponse({"success": False}, status=400)

    def post(self, request, comment_id):
        if request.method == "POST":
            comment = get_object_or_404(Comment, id=comment_id)
            if comment.likes.filter(id=request.user.id).exists():
                comment.likes.remove(request.user)
                liked = False
            else:
                comment.likes.add(request.user)
                liked = True
            return JsonResponse({
                "success": True, 
                "liked": liked, 
                "total_likes": comment.likes.count()
            })

class NotificationListView(View):
    """
    Fetch comprehensive system event streams and relation trackers for rendering.
    """
    def get(self, request):
        cutoff_date = timezone.now() - timedelta(days=30)
        notifications = request.user.notifications.select_related('sender').all()
        unread_count = request.user.notifications.filter(is_read=False).count()
        request.user.notifications.filter(is_read=False).update(is_read=True)
        request.user.notifications.filter(timestamp__lte=cutoff_date, is_read=True).delete()
        following_ids = set(request.user.following.values_list('id', flat=True))
    
        context = {
            'notifications': notifications,
            'following_ids': following_ids,
            'unread_count': unread_count
        }
        return render(request, 'posts/notification.html', context)

class CreateStory(View):
    def get(self, request):
        form = StoryForm()
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    def post(self, request):
        if request.method == "POST":
            form = StoryForm(request.POST, request.FILES)
            if form.is_valid():
                story = form.save(commit=False)
                story.author = request.user
                story.save()
                return JsonResponse({
                    'success': True,
                    'image_url': story.image.url if story.image else None,
                    'story_id': story.id
                })
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

class DeleteStory(View):
    def get(self, request):
        return JsonResponse({"success": False}, status=400)
    def post(self, request, story_id):
        if request.method == "POST":
            story = get_object_or_404(Story, id=story_id)
            if story.author == request.user:
                story.delete()
                return JsonResponse({
                    "success": True, 
                    "image_url": story.image.url, 
                    "story_id": story.id
                })

            return JsonResponse({"success": False,
                "message": "You are not allowed to delete this post."
            }, status=403)
