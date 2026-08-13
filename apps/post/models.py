from django.db import models
from django.conf import settings

class SocialPost(models.Model):
    """
    Represents an individual text or multimedia entry created by a user.
    """
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_social_posts', blank=True)

    def total_likes(self):
        """
        Calculates the aggregate number of user interactions on this specific post.
        Returns:int: The total count of users who have liked this instance.
        """
        return self.likes.count()

    def __str__(self):
        """
        Returns a trunacted summary snippet of the post's text content.
        """
        return self.content[:50]

    class Meta:
        ordering = ['-created_at']

class Comment(models.Model):
    """
    Represents a conversational message attached to a parent SocialPost instance.
    Supports nesting structures via a self-referencing hierarchy key to track individual
    replies, and features safe deletion logic via status toggles.
    """
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_comments', blank=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies'
    )
    is_deleted = models.BooleanField(default=False)
    class Meta:
        ordering = ['timestamp']


class Notification(models.Model):
    """
    Tracks and distributes automated activity system events directly to targeted users.
    """
    notification_types = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
    ]
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_notifications')
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    notification_type = models.CharField(max_length=10, choices=notification_types)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']


class Story(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stories")
    image = models.ImageField(upload_to='story/')
    timestamp = models.DateTimeField(auto_now_add=True)
    viewers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='story_viewers', blank=True)
    class Meta:
        ordering = ['-timestamp']
