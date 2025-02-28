from django.urls import path
from finder import views


urlpatterns = [
    path('recruitment-posts/', views.RecruitmentPostListCreateView.as_view(), name='recruitment-posts'),
    path('recruitment-applications/', views.RecruitmentApplicationListCreateView.as_view(), name='recruitment-applications'),
    path('team-invitations/', views.TeamInvitationListCreateView.as_view(), name='team-invitations'),
    path('recruitment-application/<uuid:pk>/', views.RecruitmentApplicationUpdateView.as_view(), name='update-recruitment-application'),
    path('team-invitation/<uuid:pk>/', views.TeamInvitationUpdateView.as_view(), name='update-team-invitation'),
    path('players/search/', views.PlayerSearchAPIView.as_view(), name='player-search'),
    path('teams/search/', views.TeamSearchAPIView.as_view(), name='team-search'),
]
