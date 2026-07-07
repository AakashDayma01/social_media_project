from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.create_post, name='create_post'),
    path('like-post/<int:post_id>/', views.like_post, name='like_post'),
    path('delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
]
