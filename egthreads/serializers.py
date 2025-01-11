from django.contrib.auth import get_user_model
from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import Thread, Comment

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

    class Meta:
        model = Thread
        fields = [
            'id', 'title', 'slug', 'content', 'author', 'game',
            'created_at', 'updated_at',
            'views', 'is_featured', 'url',
            'meta_description', 'meta_keywords'
        ]
        read_only_fields = ['slug', 'views', 'is_featured',]


class RecursiveCommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    author = UserMinimalSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'author', 'created_at', 
            'updated_at', 'likes_count', 'is_liked_by_user', 
            'replies'
        ]

    def get_replies(self, obj):
        replies = Comment.objects.filter(parent=obj)
        serializer = RecursiveCommentSerializer(replies, many=True, context=self.context)
        return serializer.data

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked_by_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

class ThreadDetailSerializer(serializers.ModelSerializer):
    author = UserMinimalSerializer(read_only=True)
    comments = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    time_since_posted = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = [
            'id', 'title', 'slug', 'content', 'author',
            'created_at', 'updated_at', 'likes_count',
            'is_liked_by_user', 'views', 'comments',
            'time_since_posted', 'meta_description',
            'meta_keywords', 'is_featured'
        ]
        read_only_fields = fields

    def get_comments(self, obj):
        # Only get top-level comments (no parent)
        comments = obj.comments.filter(parent=None)
        serializer = RecursiveCommentSerializer(comments, many=True, context=self.context)
        return serializer.data

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked_by_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

    def get_time_since_posted(self, obj):
        from django.utils import timezone
        from django.utils.timesince import timesince
        return timesince(obj.created_at, timezone.now())

