"""
Database signal receivers for the post and interaction social infrastructure.

This module listens to model lifecycle actions—such as many-to-many relationship modifications, 
database record saves, and target removals—to automatically distribute, clean up, or synchronize
in-app user activity notifications.
"""
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from apps.accounts.models import Contact
from .models import Notification, SocialPost, Comment

@receiver(m2m_changed, sender=SocialPost.likes.through)
def social_post_likes_changed(sender, instance, action, pk_set, **kwargs):
    """
    Tracks modifications to a post's like metric and handles target notification alerts.
    Generates real-time notifications when users add positive interactions, and 
    silently cleans up related entries when likes are removed.
    """
    if action == "post_add":
        for user_id in pk_set:
            if user_id != instance.author.id:
                Notification.objects.get_or_create(
                    recipient=instance.author,
                    sender_id=user_id,
                    post=instance,
                    notification_type='like'
                )
    elif action == "post_remove":
        for user_id in pk_set:
            Notification.objects.filter(
                recipient=instance.author,
                sender_id=user_id,
                post=instance,
                notification_type='like'
            ).delete()


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    """
    Triggers structured notification alerts when a user interacts through comments.
    Differentiates automatically between top-level additions aimed at the post author 
    and nested conversational replies directed towards a parent commenter.
    """
    if created:
        if instance.parent:
            recipient = instance.parent.user
            notif_type = 'comment' 
        else:
            recipient = instance.post.author
            notif_type = 'comment'

        if instance.user != recipient:
            Notification.objects.create(
                recipient=recipient,
                sender=instance.user,
                post=instance.post,
                comment=instance,
                notification_type=notif_type
            )


@receiver(post_save, sender=Contact)
def create_follow_notification(sender, instance, created, **kwargs):
    """
    Generates a social connectivity notification whenever a user follows an account.
    """
    if created:
        Notification.objects.create(
            recipient=instance.user_to,   
            sender=instance.user_from,    
            notification_type='follow'
        )

@receiver(post_delete, sender=Contact)
def delete_follow_notification(sender, instance, **kwargs):
    """
    Removes historical tracking records if a social relationship is severed.
    """
    Notification.objects.filter(
        recipient=instance.user_to,
        sender=instance.user_from,
        notification_type='follow'
    ).delete()
