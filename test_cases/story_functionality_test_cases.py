import json
from io import BytesIO
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.test import TestCase, RequestFactory
from apps.post.models import Story
from apps.post.class_view import CreateStory, DeleteStory


User = get_user_model()
class StoryClassViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="story_test_user", email="storyuser@test.com", password="Password@123",
        )
        self.other_user = User.objects.create_user(
            username="other_story_user", email="otherstory@test.com", password="Password@123",
        )
        self.factory = RequestFactory()

    def test_create_story_get(self):
        response = CreateStory().get(self.factory.get("/post/create-story/"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "Invalid request method",)

    def test_create_story_success(self):
        image = BytesIO()
        Image.new("RGB", (100, 100), "red",).save( image, format="JPEG",)
        image.seek(0)
        uploaded_image = SimpleUploadedFile("test.jpg", image.read(), content_type="image/jpeg",)
        request = self.factory.post("/post/create-story/", data={"image": uploaded_image,},)
        request.user = self.user
        response = CreateStory().post(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertIn("story_id", data,)
        self.assertIsNotNone(data["story_id"])
        self.assertIn("image_url", data)
        story = Story.objects.get(id=data["story_id"])
        self.assertEqual(story.author, self.user)
        self.assertTrue(story.image)

    def test_create_story_invalid_form(self):
        request = self.factory.post("/post/create-story/", data={})
        request.user = self.user
        response = CreateStory().post(request)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)

        self.assertFalse(data["success"])
        self.assertIn("errors", data,)

    def test_delete_story_get(self):
        request = self.factory.get("/post/delete-story/")
        request.user = self.user
        response = DeleteStory().get(request)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])

    def test_delete_story_success(self):
        image = SimpleUploadedFile(
            "test.jpg", b"fake-image-content", content_type="image/jpeg",
        )
        story = Story.objects.create(author=self.user, image=image,)
        story_id = story.id
        request = self.factory.post("/post/delete-story/")
        request.user = self.user
        response = DeleteStory().post(request, story_id=story_id,)

        self.assertEqual(response.status_code, 200,)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertIsNone(data["story_id"])
        self.assertIn("image_url", data,)
        self.assertFalse(Story.objects.filter(id=story_id).exists())

    def test_delete_story_not_owner(self):
        image = SimpleUploadedFile("test.jpg", b"fake-image-content", content_type="image/jpeg",)
        story = Story.objects.create(author=self.other_user, image=image,)
        request = self.factory.post("/post/delete-story/")
        request.user = self.user
        response = DeleteStory().post(request, story_id=story.id,)

        self.assertEqual(response.status_code, 403,)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "You are not allowed to delete this post.",)
        self.assertTrue(Story.objects.filter(id=story.id).exists())

    def test_delete_story_nonexistent_story(self):
        request = self.factory.post("/post/delete-story/")
        request.user = self.user
        
        with self.assertRaises(Http404):
            DeleteStory().post(request, story_id=999999,)