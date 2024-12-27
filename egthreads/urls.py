from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'threads', views.ThreadViewSet)

urlpatterns = router.urls

router = DefaultRouter()
router.register(r'threads', views.ThreadViewSet)
router.register(r'comments', views.CommentViewSet)

urlpatterns = [
    path('threads/<int:id>/<slug:slug>/', views.ThreadViewSet.as_view({'get': 'retrieve'})),
    path('threads/list/', views.ListThreadView.as_view(), name='thread-best-suited'),
    path('', include(router.urls)),
]

