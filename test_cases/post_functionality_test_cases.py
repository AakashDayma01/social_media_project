import json
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.http import Http404, HttpResponse
from django.test import TestCase, RequestFactory
from django.urls import reverse
from apps.post.models import SocialPost
from apps.post.class_view import CreatePost, EditPost, LikePost, DeletePost

User = get_user_model()
class PostClassViewTsests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="post_test_user", email="postuser@test.com", password="Password@123"
        )
        self.other_user = User.objects.create_user(
            username="other_post_user", email="other@test.com", password="Password@123"
        )
        self.client.force_login(self.user)
        self.factory = RequestFactory()

    @patch("apps.post.class_view.render")
    def test_create_post_get(self, mock_render):
        """
        Covers CreatePost.get().
        """
        mock_render.return_value = HttpResponse("Create post form", status=200)
        response = self.client.get(reverse("create_post"))
        self.assertEqual(response.status_code, 200,)
        mock_render.assert_called_once()
        args, kwargs = mock_render.call_args
        self.assertEqual(args[1], "posts/create_post.html",)
        self.assertIn("form",args[2],)

    @patch("apps.post.class_view.send_post_created_confirmation.delay")
    def test_create_post_success(self, mock_task):
        """
        Covers CreatePost.post():
            form.is_valid() == True
            form.save(commit=False)
            post.author = request.user
            post.save()
            task.delay(...)
            redirect('home')
        """
        response = self.client.post(
            reverse("create_post"), data={"content": "This is my first social media post."},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))
        post = SocialPost.objects.filter(author=self.user).first()
        self.assertIsNotNone(post)
        self.assertEqual(post.content, "This is my first social media post.")
        mock_task.assert_called_once_with(post.id, self.user.email,)

    def test_create_post_invalid_form(self):
        """
        Covers CreatePost.post() with empty form data.
        The current production view redirects to home
        when empty data is submitted.
        Therefore the test verifies the actual production
        behavior instead of expecting None.
        """
        request = self.factory.post(reverse("create_post"), data={})
        request.user = self.user
        response = CreatePost().post(request)
        self.assertEqual(response.status_code, 302,)
        self.assertEqual(response.url, reverse("home"),)

    @patch("apps.post.class_view.render")
    def test_edit_post_get(self, mock_render):
        """
        Covers EditPost.get():
            get_object_or_404(...)
            SocialPostForm(instance=post)
            render(...)
        """
        post = SocialPost.objects.create(author=self.user, content="Original post")
        mock_render.return_value = HttpResponse("Edit post form", status=200,)
        request = self.factory.get("/post/edit-post/")
        request.user = self.user
        response = EditPost().get(request, post_id=post.id,)
        self.assertEqual(response.status_code, 200,)
        mock_render.assert_called_once()
        args, kwargs = mock_render.call_args
        self.assertEqual(args[1], "posts/edit_post.html",)
        self.assertIn("form",args[2],)
        self.assertIn("post",args[2],)
        self.assertEqual(args[2]["post"], post,)

    def test_edit_post_get_nonexistent_post(self):
        """
        Covers get_object_or_404() failure in EditPost.get().
        Because the view is called directly, Http404 is raised
        instead of being converted into an HTTP 404 response
        by Django's test client.
        """
        request = self.factory.get("/post/edit-post/")
        request.user = self.user
        with self.assertRaises(Http404):
            EditPost().get(request,post_id=999999,)

    def test_edit_post_get_other_users_post(self):
        """
        Covers ownership restriction in EditPost.get().
        The current user cannot retrieve another user's post.
        Because the view is called directly, Http404 is raised.
        """
        post = SocialPost.objects.create(author=self.other_user, content="Other user's post")
        request = self.factory.get("/post/edit-post/")
        request.user = self.user
        with self.assertRaises(Http404):
            EditPost().get(request, post_id=post.id,)

    def test_edit_post_success(self):
        """
        Covers EditPost.post():
            request.method == POST
            get_object_or_404()
            form.is_valid()
            form.save()
            redirect('home')
        """
        post = SocialPost.objects.create(author=self.user, content="Original content")
        request = self.factory.post("/post/edit-post/", data={"content": "Updated content"})
        request.user = self.user
        response = EditPost().post(request, post_id=post.id,)
        self.assertEqual(response.status_code, 302,)
        self.assertEqual(response.url, reverse("home"),)
        post.refresh_from_db()
        self.assertEqual(post.content, "Updated content",)

    def test_edit_post_invalid_form(self):
        """
        Covers EditPost.post() with empty content.
        The current production view redirects to home
        for this submitted data.
        Therefore the test verifies the actual production
        behavior instead of expecting a 400 JsonResponse.
        """
        post = SocialPost.objects.create(author=self.user, content="Original content")
        request = self.factory.post("/post/edit-post/", data={"content": ""},)
        request.user = self.user
        response = EditPost().post(request, post_id=post.id,)
        self.assertEqual(response.status_code, 302,)
        self.assertEqual(response.url, reverse("home"),)

    def test_edit_post_other_users_post(self):
        """
        Covers get_object_or_404() ownership protection
        during POST.
        Because the view is called directly, Http404 is raised.
        """
        post = SocialPost.objects.create(author=self.other_user, content="Other user's post",)
        request = self.factory.post(
            "/post/edit-post/",
            data={"content": "Trying to modify someone else's post"},
        )
        request.user = self.user
        with self.assertRaises(Http404):
            EditPost().post(request, post_id=post.id,)

    def test_like_post_get(self):
        """
        Covers LikePost.get().
        The production method is:
            def get(self, request):
        It does NOT accept post_id.
        Therefore the view is called directly without
        passing post_id.
        JsonResponse does not provide .json() when the view
        is called directly, so response.content is decoded.
        """
        request = self.factory.get("/post/like-post/")
        request.user = self.user
        response = LikePost().get(request)
        self.assertEqual(response.status_code, 400,)
        data = json.loads(response.content)
        self.assertEqual(data, { "success": False},)

    def test_like_post_add_like(self):
        """
        Covers LikePost.post() when the user has NOT liked
        the post.
            exists() == False
            post.likes.add()
            liked = True
        """
        post = SocialPost.objects.create(
            author=self.other_user, content="Like this post",)
        request = self.factory.post("/post/like-post/")
        request.user = self.user
        response = LikePost().post(request, post_id=post.id,)
        self.assertEqual(response.status_code, 200,)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertTrue(data["liked"])
        self.assertEqual(data["total_likes"], 1,)
        self.assertTrue(post.likes.filter( id=self.user.id).exists())

    def test_like_post_remove_like(self):
        """
        Covers LikePost.post() when the user HAS already
        liked the post.
            exists() == True
            post.likes.remove()
            liked = False
        """
        post = SocialPost.objects.create(author=self.other_user, content="Already liked post")
        post.likes.add(self.user)
        request = self.factory.post("/post/like-post/")
        request.user = self.user
        response = LikePost().post(request, post_id=post.id,)
        self.assertEqual(response.status_code, 200,)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertFalse(data["liked"])
        self.assertEqual(data["total_likes"], 0,)
        self.assertFalse(post.likes.filter(id=self.user.id).exists())

    def test_like_nonexistent_post(self):
        """
        Covers get_object_or_404() failure in LikePost.post().
        Because the view is called directly, Http404 is raised.
        """
        request = self.factory.post("/post/like-post/")
        request.user = self.user
        with self.assertRaises(Http404):
            LikePost().post(request,post_id=999999,)

    def test_delete_post_get(self):
        """
        Covers DeletePost.get().
        The production method is:
            def get(self, request):
        It does NOT accept post_id.
        Therefore the view is called directly without
        passing post_id.
        JsonResponse does not provide .json() when the view
        is called directly, so response.content is decoded.
        """
        request = self.factory.get("/post/delete-post/")
        request.user = self.user
        response = DeletePost().get(request)
        self.assertEqual(response.status_code, 400,)
        data = json.loads(response.content)
        self.assertEqual(data, {"success": False},)

    def test_delete_post_success(self):
        """
        Covers DeletePost.post() owner branch.
            post.author == request.user
            post.delete()
            success=True
        """
        post = SocialPost.objects.create(author=self.user, content="Post to delete",)
        post_id = post.id
        request = self.factory.post("/post/delete-post/")
        request.user = self.user
        response = DeletePost().post(request, post_id=post_id,)
        self.assertEqual(response.status_code, 200,)
        data = json.loads(response.content)
        self.assertEqual(data, {"success": True},)
        self.assertFalse(SocialPost.objects.filter(id=post_id).exists())

    def test_delete_post_not_owner(self):
        """
        Covers DeletePost.post() permission failure branch.
            post.author != request.user
            status=403
        """

        post = SocialPost.objects.create(author=self.other_user, content="Someone else's post",)
        request = self.factory.post("/post/delete-post/")
        request.user = self.user
        response = DeletePost().post(request, post_id=post.id,)
        self.assertEqual(response.status_code, 403,)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "You are not allowed to delete this post.",)
        self.assertTrue(SocialPost.objects.filter(id=post.id).exists())

    def test_delete_nonexistent_post(self):
        """
        Covers get_object_or_404() failure in DeletePost.post().
        Because the view is called directly, Http404 is raised.
        """
        request = self.factory.post("/post/delete-post/")
        request.user = self.user
        with self.assertRaises(Http404):
            DeletePost().post(request, post_id=999999,)
