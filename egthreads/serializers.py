from rest_framework import serializers
from .models import Thread, Comment
from accounts.serializers import UserMinimalSerializer

class CommentSerializer(serializers.ModelSerializer):
    author = UserMinimalSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'created_at', 'updated_at', 'replies']

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []

class ThreadSerializer(serializers.ModelSerializer):
    author = UserMinimalSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = [
            'id', 'title', 'slug', 'content', 'author', 'game',
            'created_at', 'updated_at', 'comments_count', 'likes_count',
            'views', 'is_featured', 'is_liked', 'url',
            'meta_description', 'meta_keywords'
        ]
        read_only_fields = ['slug', 'views', 'is_featured']

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

    def get_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/threads/{obj.slug}/')
        return f'/threads/{obj.slug}/'
