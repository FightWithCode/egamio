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

class ThreadMinimalSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Thread
        fields = ['id', 'title', 'content', 'slug', 'views', 'author', 'created_at']
    
    def get_author(self, obj):
        return obj.author.name


class ThreadDetailSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    is_disliked_by_user = serializers.SerializerMethodField()
    time_since_posted = serializers.SerializerMethodField()
    related_posts = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = [
            'id', 'title', 'slug', 'content', 'author',
            'created_at', 'updated_at', 'likes_count',
            'is_liked_by_user', 'is_disliked_by_user', 'views', 'comments',
            'time_since_posted', 'meta_description',
            'meta_keywords', 'is_featured', 'related_posts', 'thread_id'
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
        print(request.user, obj.likes.all(),'--')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False
    
    def get_is_disliked_by_user(self, obj):
        request = self.context.get('request')
        print(request.user, obj.dislikes.all())
        if request and request.user.is_authenticated:
            return obj.dislikes.filter(id=request.user.id).exists()
        return False

    def get_time_since_posted(self, obj):
        from django.utils import timezone
        from django.utils.timesince import timesince
        return timesince(obj.created_at, timezone.now())
    
    def get_related_posts(self, obj):
        from django.db.models import Q

        # Split meta_keywords into individual keywords
        keywords = obj.meta_keywords.split(',')

        # Query for threads with similar keywords, excluding the current thread
        related_threads = (
            Thread.objects.filter(
                Q(meta_keywords__iregex=r'\b(' + '|'.join(keywords) + r')\b'),
                ~Q(id=obj.id)  # Exclude the current thread
            )
            .order_by('-created_at', '-views')  # Sort by created_at and views
        )

        # Limit to 3 related posts
        related_threads = related_threads[:3]

        # Serialize related threads
        serializer = ThreadMinimalSerializer(related_threads, many=True, context=self.context)
        return serializer.data

