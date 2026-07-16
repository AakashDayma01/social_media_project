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
    