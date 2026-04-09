from django.urls import path
from accounts import views

urlpatterns = [
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify-token/', views.CustomTokenVerifyView.as_view(), name='verify_token'),
    path('profile/', views.GetUserProfile.as_view(), name='user_profile'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    # path('signup/player/', views.PlayerSignupView.as_view(), name='player-signup'),
    path('signup/', views.UserSignupView.as_view(), name='user_signup'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification/', views.ResendVerificationEmailView.as_view(), name='resend_verification'),
    path('complete-profile/', views.CompleteProfile.as_view(), name='complete_profile'),
    path('profile/details/', views.PlayerProfileDetail.as_view(), name='player_profile_detail'),
    path('team/details/', views.TeamProfileDetail.as_view(), name='team_profile_detail'),
    path('password-reset/', views.PasswordResetRequest.as_view(), name='password_reset'),
    path('password-reset/confirm/', views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    path('clips/mine/', views.MyClipsList.as_view(), name='my_clips'),
    # path('signup/team/', views.TeamSignupView.as_view(), name='team-signup'),
    path('auth/google/', views.GoogleSignInView.as_view(), name='google_signin'),
    path('auth/google/step-2/', views.FinishGoogleSignup.as_view(), name='google_signin_step_2'),
]
