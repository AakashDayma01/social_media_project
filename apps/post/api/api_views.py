from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from apps.post.forms import SocialPostForm, StoryForm
from apps.post.models import SocialPost, Story, Comment
from django.http import JsonResponse
from apps.post.models import Comment
from django.utils import timezone
from django.views import View
from rest_framework import viewsets, permissions
from .serializers import SocialPostSerializer, CommentSerializer
# Create your views here.

class Post(viewsets.ModelViewSet):
    """
    Render or process the submission form for publishing a new entry.
    Binds the incoming upload assets and text values directly to the active session user.
    """
    queryset = SocialPost.objects.all()
    serializer_class = SocialPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return JsonResponse(status=status.HTTP_204_NO_CONTENT)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

class Comment(viewsets.ModelViewSet):
    """
    Render or process the submission form for publishing a new entry.
    Binds the incoming upload assets and text values directly to the active session user.
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()        
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
            'id': comment.id,
            'content': comment.content,
            'is_deleted': comment.is_deleted,
            'timestamp': comment.timestamp.strftime('%b %d, %Y %H:%M'),
            'type': 'delete'
        })

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)