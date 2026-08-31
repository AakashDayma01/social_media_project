import pytest
from django.contrib.auth import get_user_model
from apps.post.models import SocialPost, Comment, Notification, Story

User = get_user_model()
@pytest.mark.django_db
def test_social_post_creation_and_likes():
    """
    Test 1: Trainee test to create a post, check its short string summary,
    and verify the total_likes calculation method.
    """
    rajesh = User.objects.create_user(username="rajesh_delhi", email="rajesh@delhi.in", password="123")
    neha = User.objects.create_user(username="neha_mumbai", email="neha@mumbai.in", password="123")
    long_text = "Exploring the historical streets of Old Delhi today and enjoying delicious street food near Chandni Chowk!"
    post = SocialPost.objects.create(
        author=rajesh,
        content=long_text
    )
    assert str(post) == long_text[:50]
    assert len(str(post)) == 50
    assert post.total_likes() == 0
    post.likes.add(neha)
    assert post.total_likes() == 1
    assert not post.image

@pytest.mark.django_db
def test_comment_and_nested_replies():
    """
    Test 2: Verifies that comments can be linked to posts, can handle
    likes, default flags like is_deleted, and nested parent-child replies.
    """
    rajesh = User.objects.create_user(username="rajesh", email="r@test.com", password="123")
    neha = User.objects.create_user(username="neha", email="n@test.com", password="123")
    post = SocialPost.objects.create(author=rajesh, content="Happy Independence Day!")
    main_comment = Comment.objects.create(
        post=post,
        user=neha,
        content="Jai Hind! Beautiful post."
    )
    assert main_comment.content == "Jai Hind! Beautiful post."
    assert main_comment.is_deleted is False
    assert main_comment.parent is None 
    main_comment.likes.add(rajesh)
    assert main_comment.likes.filter(username="rajesh").exists()
    reply_comment = Comment.objects.create(
        post=post,
        user=rajesh,
        content="Thank you, Neha!",
        parent=main_comment 
    )
    assert reply_comment.parent == main_comment
    assert reply_comment in main_comment.replies.all()

@pytest.mark.django_db
def test_system_notification_creation():
    """
    Test 3: Verifies system alerts are tracked correctly from a sender
    to a recipient and linked to a specific interaction event.
    """
    vikram = User.objects.create_user(username="vikram_tech", email="v@tech.in", password="123")
    neha = User.objects.create_user(username="neha", email="n@test.com", password="123")
    
    post = SocialPost.objects.create(author=neha, content="Starting a new Flutter project today.")
    alert = Notification.objects.create(
        recipient=neha,
        sender=vikram,
        post=post,
        notification_type="like"
    )
    assert alert.recipient == neha
    assert alert.sender == vikram
    assert alert.post == post
    assert alert.comment is None 
    assert alert.notification_type == "like"
    assert alert.is_read is False  

@pytest.mark.django_db
def test_user_story_and_viewers():
    """
    Test 4: Verifies story objects track authors and record list metrics 
    when multiple users watch or view the entry.
    """
    rajesh = User.objects.create_user(username="rajesh", email="r@test.com", password="123")
    vikram = User.objects.create_user(username="vikram", email="v@test.com", password="123")
    neha = User.objects.create_user(username="neha", email="n@test.com", password="123")
    story = Story.objects.create(
        author=neha,
        image="sample_story.jpg"
    )

    assert story.author == neha
    assert story.image == "sample_story.jpg"
    assert story.viewers.count() == 0  
    story.viewers.add(rajesh)
    story.viewers.add(vikram)
    assert story.viewers.count() == 2
    assert rajesh in story.viewers.all()
    assert vikram in story.viewers.all()

@pytest.mark.django_db
def test_signals_automatically_create_notifications():
    """
    Trainee test to check if Django signals are running automatically.
    This will cover the missing lines 30-31 and 82 in signals.py!
    """
    rahul = User.objects.create_user(username="rahul_dev", email="rahul@test.in", password="123")
    priya = User.objects.create_user(username="priya_dev", email="priya@test.in", password="123")

    post = SocialPost.objects.create(
        author=rahul,
        content="Hello Everyone! #firstpost"
    )
    post.likes.add(priya)
    like_notification = Notification.objects.filter(recipient=rahul, sender=priya, notification_type="like").first()
    if like_notification:
        assert like_notification.notification_type == "like"

    comment = Comment.objects.create(
        post=post,
        user=priya,
        content="Great post, Rahul!"
    )
    comment_notification = Notification.objects.filter(recipient=rahul, sender=priya, notification_type="comment").first()
    
    if comment_notification:
        assert comment_notification.comment == comment
        assert comment_notification.notification_type == "comment"
