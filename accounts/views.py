import os
from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework.views import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import permission_classes
from rest_framework import permissions
from .models import UserGameProfile, Team, Role, EmailVerificationToken
from games.models import Game
from .serializers import CustomTokenObtainPairSerializer


User = get_user_model()


class UserSignupView(APIView):
    def post(self, request):
        try:
            # Get user data
            email = request.data.get('email')
            password = request.data.get('password')
            name = request.data.get('name')

            # Validate data
            if not all([email, password, name]):
                return Response({
                    'msg': 'Please provide all required fields'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if user already exists
            if User.objects.filter(email=email).exists():
                return Response({
                    'msg': 'User with this email already exists'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create user (but inactive)
            user = User.objects.create_user(
                email=email,
                password=password,
                name=name,
                is_active=False,
                is_profile_complete=False
            )

            # Create verification token
            verification_token = EmailVerificationToken.objects.create(user=user)

            # Send verification email
            self._send_verification_email(user, verification_token)

            return Response({
                'msg': 'User created successfully. Please check your email for verification.',
                'user_id': user.id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'msg': "Somthing went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def _send_verification_email(self, user, verification_token):
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{verification_token.token}"
        
        # Email subject
        subject = "Verify your email address"
        
        # Email content
        context = {
            'user': user,
            'verification_url': verification_url
        }
        
        # You'll need to create this HTML template
        html_message = render_to_string('email_templates/verify_email.html', context)
        
        # Send email
        send_mail(
            subject=subject,
            message='',
            from_email=os.getenv('EMAIL_FROM'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )


class VerifyEmailView(APIView):
    def post(self, request):
        try:
            token = request.data.get('token')
            
            # Find the verification token
            try:
                verification_token = EmailVerificationToken.objects.get(token=token)
            except EmailVerificationToken.DoesNotExist:
                return Response({
                    'msg': 'Invalid verification token'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if token is valid
            if not verification_token.is_valid():
                return Response({
                    'msg': 'Token has expired or already used'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Activate user
            user = verification_token.user
            user.is_active = True
            user.save()

            # Mark token as used
            verification_token.is_used = True
            verification_token.save()

            return Response({
                'msg': 'Email verified successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'msg': "Somthing went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationEmailView(APIView):
    def post(self, request):
        try:
            email = request.data.get('email')
            
            try:
                user = User.objects.get(email=email, is_active=False)
            except User.DoesNotExist:
                return Response({
                    'msg': 'No pending verification found for this email'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create new verification token
            verification_token = EmailVerificationToken.objects.create(user=user)

            # Send verification email
            UserSignupView()._send_verification_email(user, verification_token)

            return Response({
                'msg': 'Verification email sent successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'msg': "Somthing went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response_data = response.data
        access = response_data.pop('access', None)
        refresh = response_data.pop('refresh', None)
        # Add profile completion status to response
        user = User.objects.get(email=request.data.get('email'))
        response_data["is_profile_complete"] = user.is_profile_complete
        response_data["msg"] = "Success"
        response = Response(response_data, status=status.HTTP_200_OK)
        response.set_cookie(
            'access', access, max_age=3600, httponly=True, samesite='None', secure=True
        )
        response.set_cookie(
            'refresh', refresh, max_age=3600, httponly=True, samesite='None', secure=True
        )
        return response


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh = request.COOKIES.get('refresh')
        
        if refresh:
            request.data['refresh'] = refresh
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access = response.data.get('access')
            response.set_cookie(
                'access', access, max_age=3600, httponly=True, samesite='None', secure=True
            )
        return response


class CustomTokenVerifyView(TokenVerifyView):
    def post(self, request, *args, **kwargs):
        access = request.COOKIES.get('access')
        if access:
            request.data['token'] = access
        response = super().post(request, *args, **kwargs)
        return response


class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('access')
        response.delete_cookie('refresh')
        return response


class GoogleSignInView(APIView):
    def post(self, request):
        try:
            google_token = request.data.get('credential')
            idinfo = id_token.verify_oauth2_token(
                google_token, 
                requests.Request(), 
                settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["client_id"]
            )
            
            email = idinfo['email']
            name = idinfo.get('name', '')
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    name=name,
                    email=email,
                    is_profile_complete=False  # Set initial profile completion status
                )

            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'id': user.id,
                'full_name': user.get_full_name(),
                'is_profile_complete': user.is_profile_complete
            })

        except ValueError as e:
            return Response({'msg': "Somthing went wrong!", 'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'msg': "Somthing went wrong!", 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FinishGoogleSignup(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            if request.data.get("type") == "player":
                roles = Role.objects.filter(id__in=request.data.get('roles'))
                game = Game.objects.get(id=request.data.get('game'))
                ign = request.data.get('ign', None)
                game_data = request.data.get('game_data', {})
                preference_data = request.data.get('preference_data', {})
                # Add game profile
                ugp = UserGameProfile.objects.create(
                    user=request.user,
                    ign=ign,
                    game=game,
                    game_data=game_data,
                    preference_data=preference_data,
                )
                ugp.roles.set(roles)
                return Response({"msg": "Player signup successful"}, status=status.HTTP_200_OK)
            else:
                game = Game.objects.get(id=request.data.get('game'))
                team_name = request.data.get('team_name')
                logo = request.data.get('logo', None)
                looking_for_players = request.data.get('looking_for_players', False)

                # Create the Team
                team = Team.objects.create(
                    name=team_name,
                    created_by=request.user,
                    logo=logo,
                    game=game,
                    location=request.data.get('location', ''),
                    looking_for_players=looking_for_players,
                )
                team.save()
                request.user.save()
                return Response({"msg": "Team signup successful"}, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({'msg': "Something went wrong!", 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'msg': "Somthing went wrong!", 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CheckProfileStatus(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            'is_profile_complete': request.user.is_profile_complete
        })


class CompleteProfile(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            if request.user.is_profile_complete:
                return Response({
                    "msg": "Profile already completed"
                }, status=status.HTTP_400_BAD_REQUEST)

            profile_type = request.data.get("type")

            roles = Role.objects.filter(id__in=request.data.get('roles'))
            game = Game.objects.get(id=request.data.get('game'))
            ign = request.data.get('ign', None)
            game_data = request.data.get('game_data', {})
            preference_data = request.data.get('preference_data', {})
            
            ugp = UserGameProfile.objects.create(
                user=request.user,
                ign=ign,
                game=game,
                game_data=game_data,
                preference_data=preference_data,
            )
            ugp.roles.set(roles)

            if profile_type == "team":
                team_name = request.data.get('team_name')
                logo = request.data.get('logo', None)
                looking_for_players = request.data.get('looking_for_players', False)

                team = Team.objects.create(
                    name=team_name,
                    created_by=request.user,
                    logo=logo,
                    game=game,
                    location=request.data.get('location', ''),
                    looking_for_players=looking_for_players,
                )
                team.save()

            request.user.is_profile_complete = True
            request.user.save()

            return Response({
                "msg": f"{profile_type.capitalize()} profile completed successfully"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'msg': "Somthing went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
