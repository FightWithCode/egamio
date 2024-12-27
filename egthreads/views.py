from datetime import timedelta
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Thread, Comment
from .serializers import ThreadSerializer, CommentSerializer
from .permissions import IsAuthorOrReadOnly
from rest_framework.permissions import IsAuthenticated


class ThreadViewSet(viewsets.ModelViewSet):
    queryset = Thread.objects.all()
    serializer_class = ThreadSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    lookup_field = 'slug'
    lookup_url_kwarg = 'slug'

    def get_object(self):
        queryset = self.get_queryset()
        thread_id = self.kwargs.get('id')
        slug = self.kwargs.get('slug')
        print(thread_id, slug)
        
        obj = get_object_or_404(queryset, id=thread_id, slug=slug)
        self.check_object_permissions(self.request, obj)
        return obj
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views = F('views') + 1
        instance.save()
        # Refresh from database to get the updated views count
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def like(self, request, slug=None):
        thread = self.get_object()
        user = request.user

        if thread.likes.filter(id=user.id).exists():
            thread.likes.remove(user)
            return Response({'status': 'unliked'})
        else:
            thread.likes.add(user)
            return Response({'status': 'liked'})

    @action(detail=True)
    def comments(self, request, slug=None):
        thread = self.get_object()
        comments = thread.comments.filter(parent=None)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]

    def perform_create(self, serializer):
        """Create a new comment with the current user as author"""
        serializer.save(author=self.request.user)

    def list(self, request, *args, **kwargs):
        """List comments with optional filtering"""
        # Get query parameters
        post_id = request.query_params.get('post_id', None)
        parent_id = request.query_params.get('parent_id', None)

        queryset = self.get_queryset()

        # Filter by post if post_id is provided
        if post_id:
            queryset = queryset.filter(post_id=post_id)

        # Filter by parent comment if parent_id is provided
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        else:
            # If no parent_id, show only top-level comments
            queryset = queryset.filter(parent=None)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Get a single comment with its replies"""
        comment = self.get_object()
        serializer = self.get_serializer(comment)
        
        # Get replies for this comment
        replies = Comment.objects.filter(parent=comment)
        replies_serializer = self.get_serializer(replies, many=True)
        
        data = serializer.data
        data['replies'] = replies_serializer.data
        
        return Response(data)

    @action(detail=True, methods=['POST'])
    def reply(self, request, pk=None):
        """Add a reply to a comment"""
        parent_comment = self.get_object()
        
        # Create serializer with parent comment
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                author=request.user,
                parent=parent_comment,
                post=parent_comment.post
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['POST'])
    def like(self, request, pk=None):
        """Toggle like on a comment"""
        comment = self.get_object()
        user = request.user

        if user in comment.likes.all():
            comment.likes.remove(user)
            return Response({'status': 'unliked'})
        else:
            comment.likes.add(user)
            return Response({'status': 'liked'})

    @action(detail=True, methods=['GET'])
    def replies(self, request, pk=None):
        """Get all replies for a comment"""
        comment = self.get_object()
        replies = Comment.objects.filter(parent=comment)
        serializer = self.get_serializer(replies, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update a comment"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Delete a comment"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        """Custom queryset to include related data"""
        return Comment.objects.select_related(
            'author', 
            'parent', 
            'post'
        ).prefetch_related(
            'likes'
        )



class ListThreadView(APIView):
    def get(self, request):
        try:
            # Cache key with pagination parameters
            page = request.query_params.get('page', 1)
            per_page = request.query_params.get('per_page', 10)

            # Time window configuration
            time_window = int(request.query_params.get('days', 30))
            start_date = timezone.now() - timedelta(days=time_window)
            
            # Query with optimization and annotations
            threads = Thread.objects.select_related('author', 'category')\
                .prefetch_related('tags')\
                .filter(
                    created_at__gte=start_date,
                    is_active=True,
                    is_deleted=False
                )\
                .annotate(
                    like_count=Count('likes'),
                    comment_count=Count('comments'),
                    engagement_score=F('views') + (F('like_count') * 2) + (F('comment_count') * 3)
                )\
                .order_by('-engagement_score', '-views', '-created_at')

            # Pagination
            start_idx = (int(page) - 1) * int(per_page)
            end_idx = start_idx + int(per_page)
            paginated_threads = threads[start_idx:end_idx]

            result = {
                'data': [{
                    'id': thread.id,
                    'title': thread.title,
                    'slug': thread.slug,
                    'views': thread.views,
                    'like_count': thread.like_count,
                    'comment_count': thread.comment_count,
                    'engagement_score': thread.engagement_score,
                    'created_at': thread.created_at,
                    'author': {
                        'id': thread.author.id,
                        'name': thread.author.name,
                        'avatar': thread.author.avatar_url if hasattr(thread.author, 'avatar_url') else None
                    },
                    'category': {
                        'id': thread.category.id,
                        'name': thread.category.name,
                        'slug': thread.category.slug
                    },
                    'tags': [{'id': tag.id, 'name': tag.name} for tag in thread.tags.all()],
                    'is_trending': thread.engagement_score > settings.TRENDING_THRESHOLD
                } for thread in paginated_threads],
                'meta': {
                    'total_count': threads.count(),
                    'page': int(page),
                    'per_page': int(per_page),
                    'has_next': threads.count() > end_idx
                }
            }
            
            return Response(result)

        except Exception as e:
            return Response(
                {'error': 'Failed to fetch best suited threads', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )