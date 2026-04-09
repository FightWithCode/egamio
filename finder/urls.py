from django.urls import path
from finder import views


urlpatterns = [
    path('players/search/', views.PlayerSearchAPIView.as_view(), name='player-search'),
    path('teams/search/', views.TeamSearchAPIView.as_view(), name='team-search'),
    path('players/availability/', views.UpdatePlayerAvailability.as_view(), name='player-availability'),
    path('teams/availability/', views.UpdateTeamAvailability.as_view(), name='team-availability'),
]
