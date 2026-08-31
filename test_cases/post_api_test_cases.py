import json
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from apps.post.models import SocialPost, Comment, Story
from apps.post.api.api_views import (
PostViewset,
CommentViewset,
NotificationListView,
StoryViewset,
)

User = get_user_model()

class PostViewsetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="post_api_user", email="postapi@test.com", password="Password@123"
        )
        self.other_user = User.objects.create_user(
            username="other_post_api_user", email="otherpostapi@test.com", password="Password@123",
        )
        self.factory = APIRequestFactory()

    def test_post_viewset_create(self):
        request = self.factory.post(
            "/api/posts/", data={"content": "Test post",}, format="json",
        )
        force_authenticate(request, user=self.user)
        view = PostViewset.as_view({"post": "create",})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
        SocialPost.objects.filter(author=self.user, content="Test post").exists())

    def test_post_viewset_list(self):
        SocialPost.objects.create(author=self.user, content="First post",)
        SocialPost.objects.create(author=self.other_user, content="Second post",)
        request = self.factory.get("/api/posts/",)
        force_authenticate(request,user=self.user,)
        view = PostViewset.as_view({"get": "list",})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_viewset_retrieve(self):
        post = SocialPost.objects.create(author=self.user, content="Test post")
        request = self.factory.get(f"/api/posts/{post.id}/",)
        force_authenticate(request, user=self.user,)
        view = PostViewset.as_view({"get": "retrieve"})
        response = view(request, pk=post.id,)
        self.assertEqual(response.status_code,status.HTTP_200_OK,)
        self.assertEqual(response.data["id"], post.id)

    def test_post_viewset_partial_update(self):
        post = SocialPost.objects.create(author=self.user,content="Old content",)
        request = self.factory.patch(
            f"/api/posts/{post.id}/", data={"content": "Updated content",}, format="json",
        )
        force_authenticate(request, user=self.user,)
        view = PostViewset.as_view({"patch": "partial_update",})
        response = view(request, pk=post.id,)
        self.assertEqual(response.status_code, status.HTTP_200_OK,)
        post.refresh_from_db()
        self.assertEqual(post.content, "Updated content",)

    def test_post_viewset_delete(self):
        post = SocialPost.objects.create(author=self.user, content="Post to delete",)
        post_id = post.id
        request = self.factory.delete(f"/api/posts/{post_id}/")
        force_authenticate(request, user=self.user,)
        view = PostViewset.as_view({"delete": "destroy"})
        response = view(request, pk=post_id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SocialPost.objects.filter( id=post_id).exists())

    def test_post_viewset_like(self):
        post = SocialPost.objects.create(author=self.other_user, content="Post to like",)
        request = self.factory.post(f"/api/posts/{post.id}/like/")
        force_authenticate(request, user=self.user)
        view = PostViewset.as_view({"post": "like"})
        response = view(request, pk=post.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertTrue(response.data["liked"])
        self.assertEqual(response.data["total_likes"], 1)
        self.assertTrue(post.likes.filter(id=self.user.id).exists())

    def test_post_viewset_unlike(self):
        post = SocialPost.objects.create(author=self.other_user, content="Already liked post")
        post.likes.add(self.user)
        request = self.factory.post(f"/api/posts/{post.id}/like/")
        force_authenticate(request, user=self.user)
        view = PostViewset.as_view({"post": "like"})
        response = view(request, pk=post.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertFalse(response.data["liked"])
        self.assertEqual(response.data["total_likes"], 0)
        self.assertFalse(post.likes.filter(id=self.user.id).exists())

class CommentViewsetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="comment_api_user", email="commentapi@test.com", password="Password@123",
        )
        self.other_user = User.objects.create_user(
            username="other_comment_api_user", email="othercommentapi@test.com", password="Password@123",
        )
        self.post = SocialPost.objects.create(
            author=self.other_user, content="Post for comments",
        )
        self.factory = APIRequestFactory()

    def test_comment_viewset_create(self):
        request = self.factory.post(
            "/api/comments/",
            data={"post": self.post.id, "content": "Test comment"},
            format="json"
        )
        force_authenticate(request, user=self.user)
        view = CommentViewset.as_view({"post": "create"})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Comment.objects.filter(
                post=self.post, user=self.user, content="Test comment",
            ).exists()
        )

    def test_comment_viewset_partial_update(self):
        comment = Comment.objects.create(
            post=self.post, user=self.user, content="Old comment",
        )
        request = self.factory.patch(
            f"/api/comments/{comment.id}/",
            data={"content": "Updated comment"},
            format="json",
        )
        force_authenticate(request, user=self.user)
        view = CommentViewset.as_view({"patch": "partial_update"})
        response = view(request, pk=comment.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertEqual(comment.content, "Updated comment")

    def test_comment_viewset_delete_owner(self):
        comment = Comment.objects.create(
            post=self.post, user=self.user, content="Comment to delete"
        )
        request = self.factory.delete(f"/api/comments/{comment.id}/")
        force_authenticate(request, user=self.user)
        view = CommentViewset.as_view({"delete": "destroy"})
        response = view(request, pk=comment.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue( response.data["success"])
        self.assertTrue(response.data["is_deleted"])
        self.assertEqual(response.data["content"], "This comment has been deleted.")
        comment.refresh_from_db()
        self.assertTrue(comment.is_deleted)

    def test_comment_viewset_delete_not_owner(self):
        comment = Comment.objects.create(post=self.post, user=self.other_user, content="Other user's comment")
        request = self.factory.delete(f"/api/comments/{comment.id}/")
        force_authenticate(request, user=self.user)
        view = CommentViewset.as_view({"delete": "destroy"})
        response = view(request, pk=comment.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"], "You are not allowed to delete this comment.")
        comment.refresh_from_db()
        self.assertFalse(comment.is_deleted)

    def test_comment_viewset_like(self):
        comment = Comment.objects.create(
            post=self.post, user=self.other_user, content="Comment to like",
        )
        request = self.factory.post(f"/api/comments/{comment.id}/like/")
        force_authenticate(request, user=self.user)
        view = CommentViewset.as_view({"post": "like"})
        response = view(request, pk=comment.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK,)
        self.assertTrue(response.data["success"])
        self.assertTrue(response.data["liked"])
        self.assertEqual(response.data["total_likes"], 1)
        self.assertTrue(comment.likes.filter(id=self.user.id).exists())

    def test_comment_viewset_unlike(self):
        comment = Comment.objects.create(
            post=self.post, user=self.other_user, content="Already liked comment",
        )
        comment.likes.add(self.user)
        request = self.factory.post(f"/api/comments/{comment.id}/like/")
        force_authenticate(request, user=self.user)
        view = CommentViewset.as_view({"post": "like"})
        response = view(request, pk=comment.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertFalse(response.data["liked"])
        self.assertEqual(response.data["total_likes"], 0)

    def test_comment_viewset_get_comments(self):
        comment = Comment.objects.create(
            post=self.post, user=self.user, content="Root comment"
        )
        reply = Comment.objects.create(
            post=self.post, user=self.other_user, content="Reply comment", parent=comment
        )
        comment.likes.add(self.user)
        request = self.factory.get(f"/api/posts/{self.post.id}/comments/")
        force_authenticate(request, user=self.user)
        view = CommentViewset.as_view({"get": "get_comments"})
        response = view(request, pk=self.post.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK,)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["comments"]), 1,)
        root_comment = response.data["comments"][0]
        self.assertEqual(root_comment["id"], comment.id,)
        self.assertEqual(root_comment["content"], "Root comment")
        self.assertTrue(root_comment["liked_by_user"])
        self.assertEqual(root_comment["total_likes"], 1)
        self.assertEqual(len(root_comment["replies"]), 1)
        self.assertEqual(root_comment["replies"][0]["id"], reply.id)

class NotificationListViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="notification_api_user",
            email="notificationapi@test.com",
            password="Password@123"
        )
        self.factory = APIRequestFactory()

    def test_notification_list(self):
        request = self.factory.get("/api/notifications/")
        force_authenticate(request, user=self.user)
        view = NotificationListView.as_view({"get": "list"})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

class StoryViewsetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="story_api_user", email="storyapi@test.com", password="Password@123"
        )
        self.factory = APIRequestFactory()

    def test_story_viewset_create(self):
        request = self.factory.post("/api/stories/", data={}, format="json")
        force_authenticate(request, user=self.user)
        view = StoryViewset.as_view({"post": "create"})
        response = view(request)
        self.assertIn(
            response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
        )

    def test_story_viewset_list(self):
        request = self.factory.get( "/api/stories/")
        force_authenticate(request, user=self.user)
        view = StoryViewset.as_view({"get": "list"})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_story_viewset_delete(self):
        story = Story.objects.create(author=self.user)
        story_id = story.id
        request = self.factory.delete(f"/api/stories/{story_id}/")
        force_authenticate(request, user=self.user)
        view = StoryViewset.as_view({"delete": "destroy"})
        response = view(request, pk=story_id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Story.objects.filter(id=story_id,).exists())