from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'threads', views.ThreadViewSet)

urlpatterns = router.urls


urlpatterns = [
    path('threads/create/', views.CreateThread.as_view(), name='create_thread'),
    path('threads/list/', views.ListThreadView.as_view(), name='thread-best-suited'),
    path('threads/like/<str:thread_id>/', views.LikeThread.as_view()),
    path('threads/dislike/<str:thread_id>/', views.DislikeThread.as_view()),
    path('threads/<str:thread_id>/get-other-details/', views.GetOtherThreadDetails.as_view()),
    path('threads/<str:thread_id>/<slug:slug>/details', views.ThreadDetailView.as_view()),
    path('threads/<str:thread_id>/comment/', views.CreateCommentView.as_view(), name='create_comment'),
    path('threads/<str:thread_id>/comment/<int:comment_id>/reply/', views.ReplyToCommentView.as_view(), name='reply_to_comment'),
    path('comments/<int:comment_id>/like/', views.LikeCommentView.as_view(), name='like_comment'),
    path('comments/<int:comment_id>/dislike/', views.DislikeCommentView.as_view(), name='dislike_comment'),
    path('', include(router.urls)),
]

