from django.urls import path
from . import views

urlpatterns = [
    path("list-games", view=views.ListGames.as_view(), name="list_games"),
    path("<str:game>/roles", views.ListRoles.as_view(), name="list_game_roles"),
]
