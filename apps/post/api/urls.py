from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .api_views import Post, Comment
router = DefaultRouter()
router.register(r"post", Post, basename="post")
router.register(r"comment", Comment, basename="comment")

urlpatterns = [
    path("", include(router.urls)),
]