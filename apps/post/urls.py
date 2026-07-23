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
from . import class_view

urlpatterns = [
    path('add/', class_view.CreatePost.as_view(), name='create_post'),
    path('like-post/<int:post_id>/', class_view.LikePost.as_view(), name='like_post'),
    path('delete-post/<int:post_id>/', class_view.DeletePost.as_view(), name='delete_post'),
    path('update-post/<int:post_id>/', class_view.EditPost.as_view(), name='update_post'),
    path('comments/<int:post_id>/', class_view.GetComments.as_view(), name='get_comments'),
    path('comments/<int:post_id>/add/', class_view.AddComment.as_view(), name='add_comment'),
    path('comments/<int:post_id>/edit/', class_view.EditComments.as_view(), name='edit_comment'),
    path('comments/<int:post_id>/delete/', class_view.DeleteComment.as_view(), name='delete_comment'),
    path('like-comment/<int:comment_id>/', class_view.LikeComment.as_view(), name='like_comment'),
    path('notifications/', class_view.NotificationListView.as_view(), name='notification_list'),
    path('story-create/', class_view.CreateStory.as_view(), name='create_story'),
    path('story-delete/<int:story_id>/', class_view.DeleteStory.as_view(), name='delete_story')
 ]
    