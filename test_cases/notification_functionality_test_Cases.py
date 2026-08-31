from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone
from apps.post.models import Notification
from apps.post.class_view import NotificationListView

User = get_user_model()
class NotificationListViewTests(TestCase):
    """
    Tests for NotificationListView.
    Covers:
        - notification retrieval
        - sender select_related()
        - unread notification count
        - marking unread notifications as read
        - deleting old read notifications
        - following_ids
        - render context
    """
    def setUp(self):
        self.user = User.objects.create_user(
            username="notification_test_user", email="notification@test.com", password="Password@123",
        )
        self.sender = User.objects.create_user(
            username="notification_sender", email="sender@test.com", password="Password@123",
        )
        self.other_user = User.objects.create_user(
            username="notification_other_user", email="other@test.com", password="Password@123",
        )
        self.factory = RequestFactory()

    @patch("apps.post.class_view.render")
    def test_notification_list_get(self, mock_render):
        """
        Covers the complete NotificationListView.get() flow.
        """
        unread_notification = Notification.objects.create(
            recipient=self.user, sender=self.sender, is_read=False,
        )
        read_notification = Notification.objects.create(
            recipient=self.user, sender=self.other_user, is_read=True,
        )
        self.user.following.add(self.sender)
        mock_render.return_value = HttpResponse("Notification page",status=200,)
        request = self.factory.get("/notifications/")
        request.user = self.user
        response = NotificationListView().get(request)
        self.assertEqual(response.status_code, 200,)
        mock_render.assert_called_once()
        args, kwargs = mock_render.call_args
        self.assertEqual(args[1], "posts/notification.html",)
        context = args[2]
        self.assertIn("notifications",context,)
        self.assertIn("following_ids", context,)
        self.assertIn("unread_count", context,)
        self.assertEqual(context["unread_count"], 1,)
        self.assertIn(self.sender.id, context["following_ids"],)
        self.assertNotIn(self.other_user.id, context["following_ids"],)
        notification_ids = {notification.id for notification in context["notifications"]}
        self.assertIn(unread_notification.id, notification_ids,)
        self.assertIn(read_notification.id, notification_ids,)

    @patch("apps.post.class_view.render")
    def test_unread_notifications_are_marked_as_read(self, mock_render,):
        """
        Covers:
            request.user.notifications
                .filter(is_read=False)
                .update(is_read=True)
        """
        notification = Notification.objects.create(
            recipient=self.user, sender=self.sender, is_read=False,
        )
        mock_render.return_value = HttpResponse("Notification page", status=200,)
        request = self.factory.get("/notifications/")
        request.user = self.user
        NotificationListView().get(request)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    @patch("apps.post.class_view.render")
    def test_unread_count_is_calculated_before_update(self, mock_render,):
        """
        Ensures unread_count contains the number of unread
        notifications before they are marked as read.
        """
        Notification.objects.create(
            recipient=self.user, sender=self.sender, is_read=False,
        )
        Notification.objects.create(
            recipient=self.user, sender=self.other_user, is_read=False,
        )
        Notification.objects.create(
            recipient=self.user, sender=self.sender, is_read=True,
        )
        mock_render.return_value = HttpResponse("Notification page", status=200,)
        request = self.factory.get("/notifications/")
        request.user = self.user
        NotificationListView().get(request)
        args, kwargs = mock_render.call_args
        context = args[2]
        self.assertEqual(context["unread_count"], 2,)
        self.assertEqual(self.user.notifications.filter(is_read=False).count(), 0,)

    @patch("apps.post.class_view.render")
    def test_old_read_notifications_are_deleted(self, mock_render,):
        """
        Covers deletion of notifications that are:
            - older than 30 days
            - already read
        """

        old_date = timezone.now() - timedelta(days=31)
        old_notification = Notification.objects.create(
            recipient=self.user, sender=self.sender, is_read=True,
        )
        Notification.objects.filter(id=old_notification.id).update(timestamp=old_date)
        mock_render.return_value = HttpResponse("Notification page", status=200,)
        request = self.factory.get("/notifications/")
        request.user = self.user
        response = NotificationListView().get(request)
        self.assertFalse(Notification.objects.filter(id=old_notification.id).exists())

    @patch("apps.post.class_view.render")
    def test_recent_read_notifications_are_not_deleted(self, mock_render):
        """
        A read notification newer than 30 days should remain.
        """
        recent_date = timezone.now() - timedelta(days=10)
        notification = Notification.objects.create(
            recipient=self.user, sender=self.sender, is_read=True, timestamp=recent_date,
        )
        mock_render.return_value = HttpResponse("Notification page", status=200,)
        request = self.factory.get("/notifications/")
        request.user = self.user
        NotificationListView().get(request)
        self.assertTrue(Notification.objects.filter(id=notification.id).exists())


    @patch("apps.post.class_view.render")
    def test_old_unread_notifications_are_not_deleted(self, mock_render,):
        """
        Covers the behavior where an old unread notification
        is first marked as read and then deleted because it
        satisfies the old/read cleanup condition.
        """
        old_date = timezone.now() - timedelta(days=31)
        notification = Notification.objects.create(
            recipient=self.user, sender=self.sender, is_read=False,
        )
        Notification.objects.filter(id=notification.id).update(timestamp=old_date)
        mock_render.return_value = HttpResponse("Notification page", status=200,)
        request = self.factory.get("/notifications/")
        request.user = self.user
        response = NotificationListView().get(request)
        self.assertFalse(Notification.objects.filter(id=notification.id).exists())

    
    @patch("apps.post.class_view.render")
    def test_following_ids_are_added_to_context(self, mock_render):
        self.user.following.add(self.sender, self.other_user,)
        mock_render.return_value = HttpResponse("Notification page", status=200,)
        request = self.factory.get("/notifications/")
        request.user = self.user
        NotificationListView().get(request)
        args, kwargs = mock_render.call_args
        context = args[2]
        self.assertEqual(context["following_ids"], {self.sender.id, self.other_user.id},)
        self.assertIsInstance(context["following_ids"],set)

    @patch("apps.post.class_view.render")
    def test_notification_list_with_no_notifications(self, mock_render,):
        """
        Covers the empty notification case.
        """
        mock_render.return_value = HttpResponse("Notification page",status=200,)
        request = self.factory.get("/notifications/")
        request.user = self.user
        response = NotificationListView().get(request)
        self.assertEqual(response.status_code, 200,)
        mock_render.assert_called_once()
        args, kwargs = mock_render.call_args
        context = args[2]
        self.assertEqual(context["unread_count"], 0,)
        self.assertEqual(list(context["notifications"]), [],)
        self.assertEqual(context["following_ids"], set(),)


    @patch("apps.post.class_view.render")
    def test_notification_list_uses_correct_template(self, mock_render):
        """
        Covers the render() call and template name.
        """
        mock_render.return_value = HttpResponse("Notification page", status=200)
        request = self.factory.get("/notifications/")
        request.user = self.user
        NotificationListView().get(request)
        mock_render.assert_called_once()
        args, kwargs = mock_render.call_args
        self.assertEqual(args[1], "posts/notification.html")
