from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from smtplib import SMTPException


@shared_task(
    autoretry_for=(SMTPException, OSError),
    retry_kwargs={'max_retries': 5},
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True
)
def send_post_created_confirmation(post_id, user_email):
    return send_mail(
            'Your post has been created!',
            f'Your post with ID {post_id} has been created successfully.',
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
