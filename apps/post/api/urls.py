from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .api_views import PostViewset, CommentViewset, NotificationListView, StoryViewset
router = DefaultRouter()
router.register(r"post", PostViewset, basename="post")
router.register(r"comment", CommentViewset, basename="comment")
router.register(r"notifications", NotificationListView, basename="notifications")
router.register(r"story", StoryViewset, basename="story")

urlpatterns = [
    path("", include(router.urls)),
]
