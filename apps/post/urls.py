"""
URL configuration for the post and interaction social features.

This module maps incoming HTTP request routes to their corresponding view functions 
handling feed management, content creation, nested commenting, engagement metrics, 
and user notifications.

Routes:
    - add/ : Creates and publishes new social posts.
    - like-post/<post_id>/ : Toggles likes on individual posts.
    - delete-post/<post_id>/ : Permanently removes an existing post.
    - update-post/<post_id>/ : Modifies content or attachments of an existing post.
    - comments/<post_id>/ : Fetches the conversation list for a specific post.
    - comments/<post_id>/add/ : Publishes top-level comments or nested replies.
    - comments/<post_id>/edit/ : Modifies an existing comment entry.
    - comments/<post_id>/delete/ : Flags or hard-deletes a comment entry.
    - like-comment/<comment_id>/ : Toggles like status on an individual comment.
    - notifications/ : Displays structural user activity feeds.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.create_post, name='create_post'),
    path('like-post/<int:post_id>/', views.like_post, name='like_post'),
    path('delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('update-post/<int:post_id>/', views.edit_post, name='update_post'),
    path('comments/<int:post_id>/', views.get_comments, name='get_comments'),
    path('comments/<int:post_id>/add/', views.add_comment, name='add_comment'),
    path('comments/<int:post_id>/edit/', views.edit_comment, name='edit_comment'),
    path('comments/<int:post_id>/delete/', views.delete_comment, name='delete_comment'),
    path('like-comment/<int:comment_id>/', views.like_comment, name='like_comment'),
    path('notifications/', views.notification_list_view, name='notification_list'),
 ]
    