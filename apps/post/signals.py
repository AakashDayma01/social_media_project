from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from apps.accounts.models import Contact
from .models import Notification, SocialPost, Comment

@receiver(m2m_changed, sender=SocialPost.likes.through)
def social_post_likes_changed(sender, instance, action, pk_set, **kwargs):
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
    if created:
        Notification.objects.create(
            recipient=instance.user_to,   
            sender=instance.user_from,    
            notification_type='follow'
        )

@receiver(post_delete, sender=Contact)
def delete_follow_notification(sender, instance, **kwargs):
    Notification.objects.filter(
        recipient=instance.user_to,
        sender=instance.user_from,
        notification_type='follow'
    ).delete()
