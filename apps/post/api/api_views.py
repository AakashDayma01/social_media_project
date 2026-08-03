from django.shortcuts import render, redirect, get_object_or_404
from apps.post.models import SocialPost, Story, Comment, Notification
from rest_framework.response import Response
from apps.post.models import Comment
from django.utils import timezone
from rest_framework import viewsets, permissions
from apps.post.pagination import PostPagination, CommentPagination
from rest_framework.decorators import action
from .serializers import SocialPostSerializer, CommentSerializer, NotificationSerializer, StorySerializer
# Create your views here.

class PostViewset(viewsets.ModelViewSet):
    """
    Render or process the submission form for publishing a new entry.
    Binds the incoming upload assets and text values directly to the active session user.
    """
    queryset = SocialPost.objects.all()
    serializer_class = SocialPostSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PostPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        post = self.get_object()
        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
        return Response({
            'success': True,
            'liked': liked,
            'total_likes': post.likes.count()
        })

class CommentViewset(viewsets.ModelViewSet):
    """
    Render or process the submission form for publishing a new entry.
    Binds the incoming upload assets and text values directly to the active session user.
    """ 
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CommentPagination
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()        
        if comment.user != request.user:
            return Response({'success': False, 
                'error': 'You are not allowed to delete this comment.'
            }, status=403)

        comment.content = 'This comment has been deleted.'
        comment.is_deleted = True
        comment.likes.clear()
        comment.timestamp = timezone.now()
        comment.save()
        return Response({
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

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        comment = self.get_object()
        if comment.likes.filter(id=request.user.id).exists():
            comment.likes.remove(request.user)
            liked = False
        else:
            comment.likes.add(request.user)
            liked = True
        return Response({
            "success": True, 
            "liked": liked, 
            "total_likes": comment.likes.count()
        })



class NotificationListView(viewsets.ModelViewSet):
    """
    Fetch comprehensive system event streams and relation trackers for rendering.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

class StoryViewset(viewsets.ModelViewSet):
    queryset = Story.objects.all()
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
            serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)