import json
from django.contrib.auth import get_user_model
from django.http import Http404
from django.test import TestCase, RequestFactory
from django.urls import reverse
from apps.post.models import SocialPost, Comment
from apps.post.class_view import AddComment, EditComments, GetComments, DeleteComment, LikeComment


User = get_user_model()

class CommentClassViewTests(TestCase):
    """
    Complete coverage tests for:
        - AddComment
        - EditComments
        - GetComments
        - DeleteComment
        - LikeComment

    Covers:
        - GET branches
        - successful comment creation
        - nested comments/replies
        - invalid/nonexistent objects
        - comment ownership
        - successful edit
        - successful delete
        - deleted comment state
        - like -> unlike branches
        - comment tree construction
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="comment_test_user",email="commentuser@test.com",password="Password@123",
        )

        self.other_user = User.objects.create_user(
            username="other_comment_user", email="othercomment@test.com", password="Password@123"
        )
        self.post = SocialPost.objects.create(author=self.user, content="Test social media post",)
        self.other_post = SocialPost.objects.create(author=self.other_user, content="Another social media post",)
        self.client.force_login(self.user)
        self.factory = RequestFactory()

    def test_add_comment_get(self):
        """
        Covers AddComment.get().
        """
        request = self.factory.get("/post/add-comment/")
        request.user = self.user
        response = AddComment().get(request)
        self.assertEqual(response.status_code,200,)
        data = json.loads(response.content)
        self.assertEqual(data,{"success": False, "error": "Invalid request method",},)

    def test_add_comment_success(self):
        """
        Covers AddComment.post() for a top-level comment.
        """
        request = self.factory.post(
            "/post/add-comment/", data={"content": "This is my comment.",},
        )
        request.user = self.user
        response = AddComment().post(request, post_id=self.post.id,)
        self.assertEqual(response.status_code, 200,)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertIn("id", data,)
        self.assertEqual(data["username"], self.user.username,)
        self.assertEqual(data["content"], "This is my comment.",)
        self.assertIsNone(data["parent_id"])
        self.assertEqual(data["type"], "add",)
        self.assertFalse(data["liked_by_user"])
        self.assertEqual(data["total_likes"], 0,)
        comment = Comment.objects.get(id=data["id"])
        self.assertEqual(comment.post, self.post,)
        self.assertEqual(comment.user, self.user,)
        self.assertEqual( comment.content,"This is my comment.", )
        self.assertIsNone(comment.parent)

    def test_add_comment_reply(self):
        """
        Covers AddComment.post() with a parent comment.
        """
        parent_comment = Comment.objects.create(
            post=self.post,user=self.user,content="Parent comment",
        )
        request = self.factory.post("/post/add-comment/",
            data={
                "content": "This is a reply.", "parent": parent_comment.id,
            },
        )
        request.user = self.user
        response = AddComment().post(request, post_id=self.post.id,)
        self.assertEqual(response.status_code, 200,)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["content"],"This is a reply.",)
        self.assertEqual(data["parent_id"],str(parent_comment.id),)
        reply = Comment.objects.get( id=data["id"])
        self.assertEqual(reply.parent, parent_comment,)

    def test_add_comment_nonexistent_post(self):
        """
        Covers get_object_or_404() failure in AddComment.post().
        """
        request = self.factory.post("/post/add-comment/",data={"content": "Comment on missing post",},)
        request.user = self.user
        with self.assertRaises(Http404):
            AddComment().post(request, post_id=999999,)

    def test_add_comment_nonexistent_parent(self):
        """
        Covers get_object_or_404() failure for parent comment.
        """
        request = self.factory.post(
            "/post/add-comment/",
            data={"content": "Reply to missing comment", "parent": 999999,},
        )
        request.user = self.user
        with self.assertRaises(Http404):
            AddComment().post( request, post_id=self.post.id,)

    def test_edit_comment_get(self):
        """
        Covers EditComments.get().
        """
        request = self.factory.get("/post/edit-comment/")
        request.user = self.user
        response = EditComments().get(request)
        self.assertEqual(response.status_code, 200,)
        data = json.loads(response.content)
        self.assertEqual(
            data, {"success": False, "error": "Invalid request method",},
        )

    def test_edit_comment_success(self):
        """
        Covers successful EditComments.post().
        """
        comment = Comment.objects.create(
            post=self.post, user=self.user, content="Original comment",
        )
        request = self.factory.post(
            "/post/edit-comment/",
            data={"parent": comment.id, "content": "Updated comment",},
        )
        request.user = self.user
        response = EditComments().post(request,post_id=self.post.id,)
        self.assertEqual(response.status_code,200,)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["id"],comment.id,)
        self.assertEqual(data["username"], self.user.username,)
        self.assertEqual(data["content"], "Updated comment",)
        self.assertEqual(data["type"], "edit",)
        self.assertEqual(data["total_likes"], 0,)
        comment.refresh_from_db()
        self.assertEqual(comment.content, "Updated comment",)

    def test_edit_comment_not_owner(self):
        """
        Covers EditComments.post() permission failure.
        """
        comment = Comment.objects.create(post=self.post, user=self.other_user, content="Other user's comment")
        request = self.factory.post(
            "/post/edit-comment/",
            data={"parent": comment.id,"content": "Trying to edit another user's comment",},
        )
        request.user = self.user
        response = EditComments().post(request, post_id=self.post.id,)
        self.assertEqual(response.status_code, 403,)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "You are not allowed to edit this comment.",)
        comment.refresh_from_db()
        self.assertEqual(comment.content, "Other user's comment",)

    def test_edit_comment_nonexistent_post(self):
        """
        Covers get_object_or_404() failure for post.
        """
        request = self.factory.post(
            "/post/edit-comment/",data={"parent": 999999, "content": "Updated",}
        )
        request.user = self.user
        with self.assertRaises(Http404):
            EditComments().post(request, post_id=999999,)

    def test_edit_comment_nonexistent_comment(self):
        """
        Covers get_object_or_404() failure for comment.
        """
        request = self.factory.post(
            "/post/edit-comment/",
            data={"parent": 999999, "content": "Updated",},
        )
        request.user = self.user
        with self.assertRaises(Http404):
            EditComments().post(request, post_id=self.post.id,)

    def test_edit_comment_from_different_post(self):
        """
        Covers comment lookup restricted by post=post.
        """
        comment = Comment.objects.create(
            post=self.other_post, user=self.user, content="Comment belongs to another post",
        )

        request = self.factory.post(
            "/post/edit-comment/",
            data={"parent": comment.id, "content": "Trying to edit",},
        )
        request.user = self.user
        with self.assertRaises(Http404):
            EditComments().post(request, post_id=self.post.id,)

    def test_get_comments_success_empty(self):
        """
        Covers GetComments.get() with no comments.
        """
        request = self.factory.get("/post/comments/")
        request.user = self.user
        response = GetComments().get(request, post_id=self.post.id,)
        self.assertEqual(response.status_code, 200,)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["comments"], [],)

    def test_get_comments_root_comment(self):
        """
        Covers a top-level comment in the comment tree.
        """
        comment = Comment.objects.create(post=self.post, user=self.user, content="Root comment")
        request = self.factory.get("/post/comments/")
        request.user = self.user
        response = GetComments().get(request, post_id=self.post.id,)
        self.assertEqual(response.status_code, 200,)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(len(data["comments"]), 1,)
        root = data["comments"][0]
        self.assertEqual(root["id"], comment.id,)
        self.assertEqual(root["username"], self.user.username,)
        self.assertEqual(root["content"],"Root comment",)
        self.assertFalse(root["liked_by_user"])
        self.assertEqual(root["total_likes"], 0,)
        self.assertFalse(root["is_deleted"])
        self.assertEqual(root["replies"],[],)

    def test_get_comments_nested_replies(self):
        """
        Covers recursive attach_replies() logic.
        """
        root = Comment.objects.create(
            post=self.post, user=self.user, content="Root comment",
        )
        reply = Comment.objects.create(
            post=self.post, user=self.other_user, content="First reply", parent=root,
        )
        nested_reply = Comment.objects.create(
            post=self.post, user=self.user, content="Nested reply", parent=reply,
        )
        request = self.factory.get("/post/comments/")
        request.user = self.user
        response = GetComments().get(request, post_id=self.post.id,)
        self.assertEqual(response.status_code, 200,)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(len(data["comments"]), 1,)
        root_data = data["comments"][0]
        self.assertEqual(root_data["id"], root.id,)
        self.assertEqual(len(root_data["replies"]), 1,)
        reply_data = root_data["replies"][0]
        self.assertEqual(reply_data["id"], reply.id,)
        self.assertEqual(reply_data["content"], "First reply",)
        self.assertEqual(len(reply_data["replies"]), 1,)
        nested_data = reply_data["replies"][0]
        self.assertEqual(nested_data["id"], nested_reply.id,)
        self.assertEqual(nested_data["content"],"Nested reply",)
        self.assertEqual(nested_data["replies"], [],)

    def test_get_comments_liked_comment(self):
        """
        Covers liked_by_user == True branch.
        """
        comment = Comment.objects.create(
            post=self.post, user=self.other_user, content="Liked comment",
        )
        comment.likes.add(self.user)
        request = self.factory.get("/pot/comments/")
        request.user = self.user
        response = GetComments().get(request, post_id=self.post.id,)
        data = json.loads(response.content)
        comment_data = data["comments"][0]
        self.assertTrue(comment_data["liked_by_user"])
        self.assertEqual(comment_data["total_likes"], 1,)

    def test_get_comments_deleted_comment(self):
        """
        Covers is_deleted in returned comment data.
        """
        comment = Comment.objects.create(
            post=self.post, user=self.user, content="Deleted comment", is_deleted=True,
        )
        request = self.factory.get("/post/comments/")
        request.user = self.user
        response = GetComments().get(request, post_id=self.post.id,)
        data = json.loads(response.content)
        comment_data = data["comments"][0]
        self.assertTrue(comment_data["is_deleted"])

    def test_get_comments_nonexistent_post(self):
        """
        Covers get_object_or_404() failure in GetComments.get().
        """
        request = self.factory.get("/post/comments/")
        request.user = self.user
        with self.assertRaises(Http404):
            GetComments().get(request, post_id=999999,)

    
    def test_delete_comment_add_method(self):
        """
        Covers the existing DeleteComment.add() method.
        Note:
            The production code calls this method 'add', not 'get'.
        """
        request = self.factory.get("/post/delete-comment/")
        request.user = self.user
        response = DeleteComment().add(request)
        self.assertEqual(response.status_code, 200,)
        data = json.loads(response.content)
        self.assertEqual(
            data, {"success": False, "error": "Invalid request method",},
        )

    def test_delete_comment_success(self):
        """
        Covers successful DeleteComment.post().
        """
        comment = Comment.objects.create(
            post=self.post, user=self.user, content="Comment to delete",
        )
        comment.likes.add(self.other_user)
        request = self.factory.post(
            "/post/delete-comment/",data={"comment_id": comment.id,},
        )
        request.user = self.user
        response = DeleteComment().post(request, post_id=self.post.id,)
        self.assertEqual(response.status_code, 200,)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["id"], str(comment.id),)
        self.assertEqual(data["content"], "This comment has been deleted.",)
        self.assertTrue(data["is_deleted"])
        self.assertEqual(data["type"], "delete",)
        comment.refresh_from_db()
        self.assertEqual(comment.content, "This comment has been deleted.",)
        self.assertTrue(comment.is_deleted)
        self.assertEqual(comment.likes.count(), 0,)

    def test_delete_comment_not_owner(self):
        """
        Covers DeleteComment.post() permission failure.
        """
        comment = Comment.objects.create(
            post=self.post, user=self.other_user, content="Someone else's comment",
        )

        request = self.factory.post(
            "/post/delete-comment/", data={ "comment_id": comment.id,},
        )
        request.user = self.user
        response = DeleteComment().post(request, post_id=self.post.id,)
        self.assertEqual(response.status_code, 403,)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertEqual(
            data["error"], "You are not allowed to delete this comment.",
        )
        comment.refresh_from_db()
        self.assertEqual(comment.content, "Someone else's comment",)
        self.assertFalse(comment.is_deleted)

    def test_delete_comment_nonexistent_post(self):
        """
        Covers get_object_or_404() failure for post.
        """
        request = self.factory.post(
            "/post/delete-comment/", data={"comment_id": 999999,},
        )
        request.user = self.user
        with self.assertRaises(Http404):
            DeleteComment().post(request, post_id=999999,)

    def test_delete_comment_nonexistent_comment(self):
        """
        Covers get_object_or_404() failure for comment.
        """
        request = self.factory.post("/post/delete-comment/", data={"comment_id": 999999,},)
        request.user = self.user
        with self.assertRaises(Http404):
            DeleteComment().post(request, post_id=self.post.id,)

    def test_like_comment_get(self):
        """
        Covers LikeComment.get().
        """
        request = self.factory.get("/post/like-comment/")
        request.user = self.user
        response = LikeComment().get(request)
        self.assertEqual(response.status_code, 400,)
        data = json.loads(response.content)
        self.assertEqual(data, {"success": False},)

    def test_like_comment_add_like(self):
        """
        Covers LikeComment.post() when user has not
        already liked the comment.
        """
        comment = Comment.objects.create(
            post=self.post, user=self.other_user, content="Comment to like"
        )
        request = self.factory.post("/post/like-comment/")
        request.user = self.user
        response = LikeComment().post(request, comment_id=comment.id,)
        self.assertEqual(response.status_code, 200,)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertTrue(data["liked"])
        self.assertEqual(data["total_likes"], 1,)
        self.assertTrue(comment.likes.filter(id=self.user.id).exists())

    def test_like_comment_remove_like(self):
        """
        Covers LikeComment.post() when user has
        already liked the comment.
        """
        comment = Comment.objects.create(
            post=self.post, user=self.other_user, content="Already liked comment",
        )
        comment.likes.add(self.user)
        request = self.factory.post("/post/like-comment/")
        request.user = self.user
        response = LikeComment().post(request, comment_id=comment.id,)
        self.assertEqual(response.status_code,200,)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertFalse(data["liked"])
        self.assertEqual(data["total_likes"], 0,)
        self.assertFalse(comment.likes.filter(id=self.user.id).exists())

    def test_like_comment_nonexistent_comment(self):
        """
        Covers get_object_or_404() failure in LikeComment.post().
        """
        request = self.factory.post("/post/like-comment/")
        request.user = self.user
        with self.assertRaises( Http404):
            LikeComment().post(request, comment_id=999999,)
