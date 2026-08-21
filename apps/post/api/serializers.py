from apps.post.models import SocialPost, Comment, Notification, Story
from rest_framework import serializers
from django.contrib.auth import get_user_model
class SocialPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialPost
        fields = "__all__"
        read_only_fields = ['author']

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'user', 'content',
            'timestamp', 'likes', 'parent',
            'is_deleted', 'replies'
        ]
        read_only_fields = ['timestamp', 'is_deleted', 'likes', 'user']

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.filter(is_deleted=False), many=True, context=self.context).data
        return []

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class NotificationSenderSerializer(serializers.ModelSerializer):
    """
    A minimal user serializer to avoid leaking sensitive data
    while showing who triggered the notification.
    """
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'first_name', 'last_name']


class NotificationSerializer(serializers.ModelSerializer):
    sender = NotificationSenderSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'recipient',
            'sender',
            'post',
            'comment',
            'notification_type',
            'timestamp',
            'is_read'
        ]
        read_only_fields = ['recipient', 'sender', 'timestamp','notification_type']


class StorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = [
            'id',
            'author',
            'image',
            'timestamp',
            'viewers'
        ]
        read_only_fields = ['viewers', 'timestamp', 'author']
