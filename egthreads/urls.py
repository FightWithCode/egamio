from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'threads', views.ThreadViewSet)

urlpatterns = router.urls


urlpatterns = [
    path('threads/list/', views.ListThreadView.as_view(), name='thread-best-suited'),
    path('threads/like/<str:thread_id>/', views.LikeThread.as_view()),
    path('threads/dislike/<str:thread_id>/', views.DislikeThread.as_view()),
    path('threads/<str:thread_id>/<slug:slug>', views.ThreadDetailView.as_view()),
    path('', include(router.urls)),
]

