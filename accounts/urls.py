from django.urls import path
from accounts import views

urlpatterns = [
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify-token/', views.CustomTokenVerifyView.as_view(), name='verify_token'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    # path('signup/player/', views.PlayerSignupView.as_view(), name='player-signup'),
    path('signup/', views.UserSignupView.as_view(), name='user_signup'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification/', views.ResendVerificationEmailView.as_view(), name='resend_verification'),
    path('complete-profile/', views.CompleteProfile.as_view(), name='complete_profile'),
    # path('signup/team/', views.TeamSignupView.as_view(), name='team-signup'),
    path('auth/google/', views.GoogleSignInView.as_view(), name='google_signin'),
    path('auth/google/step-2/', views.FinishGoogleSignup.as_view(), name='google_signin_step_2'),
]
