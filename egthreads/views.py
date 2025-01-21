from datetime import timedelta
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.utils import timezone
from django.conf import settings
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from .models import Thread, Comment
from .serializers import ThreadSerializer, CommentSerializer, ThreadDetailSerializer, RecursiveCommentSerializer, ReplySerializer, ThreadCreateSerializer
from .permissions import IsAuthorOrReadOnly


class ThreadViewSet(viewsets.ModelViewSet):
    queryset = Thread.objects.all()
    serializer_class = ThreadSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    lookup_field = 'thread_id'
    lookup_url_kwarg = 'thread_id'

    def get_object(self):
        queryset = self.get_queryset()
        thread_id = self.kwargs.get('thread_id')
        
        obj = get_object_or_404(queryset, thread_id=thread_id)
        self.check_object_permissions(self.request, obj)
        return obj
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


    @action(detail=True, methods=['post'])
    def like(self, request, thread_id=None):
        thread = self.get_object()
        user = request.user

        if thread.likes.filter(id=user.id).exists():
            thread.likes.remove(user)
            return Response({'status': 'disliked'})
        else:
            thread.likes.add(user)
            return Response({'status': 'liked'})

class CreateThread(APIView):
    def post(self, request):
        response = {}
        try:
            serializer = ThreadCreateSerializer(
                data=request.data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                thread = serializer.save()
                response["msg"] = 'Thread created successfully'
                response["thread"] = {
                    'thread_id': thread.thread_id,
                    'slug': thread.slug,
                    'title': thread.title
                }
                return Response(response, status=status.HTTP_201_CREATED)
            else:
                response["error"] = serializer.errors
                response["msg"] = "Validation error"
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response["error"] = str(e)
            response["msg"] = "Something went wrong"
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


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
            return Response({'status': 'disliked'})
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


class ThreadDetailView(generics.RetrieveAPIView):
    queryset = Thread.objects.all()
    serializer_class = ThreadDetailSerializer
    permission_classes = [IsAuthorOrReadOnly]
    lookup_field = 'thread_id'

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        Thread.objects.filter(thread_id=instance.thread_id).update(views=F('views') + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class GetOtherThreadDetails(APIView):

    def get(self, request, thread_id):
        response = {}
        try:
            print(request.user, '-----------')
            thread_obj = Thread.objects.get(thread_id=thread_id)
            comments = thread_obj.comments.filter(parent=None)
            serializer = RecursiveCommentSerializer(comments, many=True, context={"request": request})
            response["comments"] = serializer.data
            response["liked"] = False
            response["disliked"] = False
            if request.user.is_authenticated:
                response["liked"] = thread_obj.likes.filter(id=request.user.id).exists()
            if request and request.user.is_authenticated:
                response["disliked"] = thread_obj.dislikes.filter(id=request.user.id).exists()
            response["msg"] = "fetched"
            print(response)
            return Response(response, status=status.HTTP_200_OK)
        except Thread.DoesNotExist:
            response["msg"] = "Thread not found"
            response["error"] = "Thread not found"
            return Response(response, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            response["msg"] = "Something went wrong"
            response["error"] = str(e)
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            threads = Thread.objects.select_related('author', 'game')\
                .filter(
                    created_at__gte=start_date,
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
                    'thread_id': thread.thread_id,
                    'title': thread.title,
                    'slug': thread.slug,
                    'views': thread.views,
                    'like_count': thread.like_count,
                    'comment_count': thread.comment_count,
                    'engagement_score': thread.engagement_score,
                    'created_at': thread.created_at,
                    'game': thread.game.name,
                    'short_content': thread.content,
                    'author': {
                        'id': thread.author.id,
                        'name': thread.author.name,
                        'avatar': thread.author.avatar_url if hasattr(thread.author, 'avatar_url') else None
                    },
                    # 'tags': [{'id': tag.id, 'name': tag.name} for tag in thread.meta_keywords.all()],
                    'is_trending': thread.engagement_score > 200
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


class LikeThread(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, thread_id):
        """Toggle like on a Thread"""
        try:
            thread = Thread.objects.get(thread_id=thread_id)

            if request.user in thread.likes.all():
                thread.likes.remove(request.user)
                thread.save()
                return Response({'status': 'removed'})
            else:
                thread.likes.add(request.user)
                thread.dislikes.remove(request.user)
                thread.save()
                return Response({'status': 'liked'})
        except Thread.DoesNotExist:
            return Response({'msg': 'Thread not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'msg': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DislikeThread(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, thread_id):
        """Toggle like on a Thread"""
        try:
            thread = Thread.objects.get(thread_id=thread_id)

            if request.user in thread.dislikes.all():
                thread.dislikes.remove(request.user)
                thread.save()
                return Response({'status': 'removed'})
            else:
                thread.dislikes.add(request.user)
                thread.likes.remove(request.user)
                thread.save()   
                return Response({'status': 'disliked'})
        except Thread.DoesNotExist:
            return Response({'msg': 'Thread not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'msg': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateCommentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, thread_id):
        thread = get_object_or_404(Thread, thread_id=thread_id)
        content = request.data.get('content')

        if not content:
            return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Create the comment
        comment = Comment.objects.create(
            thread=thread,
            content=content,
            author=request.user
        )

        # Serialize and return the comment
        comments = thread.comments.filter(parent=None)
        serializer = RecursiveCommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReplyToCommentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, thread_id, comment_id):
        try:
            # Fetch the thread and comment
            thread = Thread.objects.get(thread_id=thread_id)
            parent_comment = Comment.objects.get(id=comment_id, thread=thread)

            # Prepare the data for the new reply
            reply_data = {
                'content': request.data.get('content'),
                'parent': parent_comment.id,
                'thread': thread.id,
                'author': request.user.id  # Set the logged-in user as the author
            }

            # Serialize and validate the reply data
            serializer = ReplySerializer(data=reply_data)
            if serializer.is_valid():
                # Save the new reply
                reply = serializer.save()

                # Return the serialized reply data
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Thread.DoesNotExist:
            return Response({"detail": "Thread not found."}, status=status.HTTP_404_NOT_FOUND)
        except Comment.DoesNotExist:
            return Response({"detail": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)


class LikeCommentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        user = request.user

        # If user has already liked the comment, remove the like
        if user in comment.likes.all():
            comment.likes.remove(user)
            return Response({'status': 'unliked'}, status=status.HTTP_200_OK)
        else:
            # Add like to the comment
            comment.likes.add(user)
            if user in comment.dislikes.all():
                comment.dislikes.remove(user)  # Remove dislike if the user liked the comment
            return Response({'status': 'liked'}, status=status.HTTP_200_OK)


class DislikeCommentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        user = request.user

        # If user has already disliked the comment, remove the dislike
        if user in comment.dislikes.all():
            comment.dislikes.remove(user)
            return Response({'status': 'undisliked'}, status=status.HTTP_200_OK)
        else:
            # Add dislike to the comment
            comment.dislikes.add(user)
            if user in comment.likes.all():
                comment.likes.remove(user)  # Remove like if the user disliked the comment
            return Response({'status': 'disliked'}, status=status.HTTP_200_OK)

