from django.urls import path
from accounts import views

urlpatterns = [
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('signup/player/', views.PlayerSignupView.as_view(), name='player-signup'),
    path('signup/team/', views.TeamSignupView.as_view(), name='team-signup'),
]
