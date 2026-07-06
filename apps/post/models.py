from django.db import models
from django.conf import settings

class SocialPost(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_social_posts', blank=True)

    def total_likes(self):
        return self.likes.count()

    def __str__(self):
        return self.content[:50]

    class Meta:
        ordering = ['-created_at']
