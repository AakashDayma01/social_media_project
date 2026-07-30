from apps.post.models import SocialPost, Comment
from rest_framework import serializers
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

