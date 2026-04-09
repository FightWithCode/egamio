from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import permission_classes
from rest_framework import permissions
from .models import UserGameProfile, Team, Role, EmailVerificationToken, UserShort
from games.models import Game
from .serializers import CustomTokenObtainPairSerializer, UserShortSerializer, UserGameProfileSerializer, TeamProfileSerializer


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
            try:
                self._send_verification_email(user, verification_token)
            except Exception:
                verification_token.delete()
                user.delete()
                raise

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
            from_email=settings.DEFAULT_FROM_EMAIL,
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
            'access', access, max_age=3600 * 24, httponly=True, samesite='None', secure=True
        )
        response.set_cookie(
            'refresh', refresh, max_age=3600 * 24 * 7, httponly=True, samesite='None', secure=True
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
                'access', access, max_age=3600 * 24, httponly=True, samesite='None', secure=True
            )
        return response


class CustomTokenVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        access = request.COOKIES.get('access')
        if access:
            request.data['token'] = access
        response = super().post(request, *args, **kwargs)
        return response


class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(
            'access',
            samesite='None',
        )
        response.delete_cookie(
            'refresh',
            samesite='None',
        )
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
            looking_for_team = request.data.get('looking_for_team', False)
            
            ugp = UserGameProfile.objects.create(
                user=request.user,
                ign=ign,
                game=game,
                game_data=game_data,
                preference_data=preference_data,
                looking_for_team=looking_for_team,
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
                if roles.exists():
                    team.roles_needed.set(roles)
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

class GetUserProfile(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            user_profile = {
                'id': user.id,
                'full_name': user.get_full_name(),
                'is_profile_complete': user.is_profile_complete,
                'email': user.email,
                'location': user.location,
            }
            return Response(user_profile, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'msg': "Somthing went wrong!",
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class MyClipsList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            clips = UserShort.objects.filter(user=request.user).order_by('-created_at')
            serializer = UserShortSerializer(clips, many=True, context={'request': request})
            return Response({'msg': 'fetched', 'data': serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'msg': "Somthing went wrong!",
                'error': str(e),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _parse_roles(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [int(item) for item in value if str(item).isdigit()]
    if isinstance(value, str):
        return [int(item) for item in value.split(",") if item.strip().isdigit()]
    return []


class PlayerProfileDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        profile = UserGameProfile.objects.filter(user=request.user).select_related('game', 'user').prefetch_related('roles').first()
        if not profile:
            return Response({"msg": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserGameProfileSerializer(profile, context={'request': request})
        return Response({
            "msg": "fetched",
            "user": {
                "id": request.user.id,
                "name": request.user.name,
                "email": request.user.email,
                "location": request.user.location,
            },
            "profile": serializer.data,
        }, status=status.HTTP_200_OK)

    def patch(self, request):
        profile = UserGameProfile.objects.filter(user=request.user).select_related('game', 'user').prefetch_related('roles').first()
        if not profile:
            return Response({"msg": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

        name = request.data.get("name")
        location = request.data.get("location")
        if name is not None:
            request.user.name = name
        if location is not None:
            request.user.location = location
        if name is not None or location is not None:
            request.user.save(update_fields=["name", "location"])

        ign = request.data.get("ign")
        experience = request.data.get("experience")
        looking_for_team = _parse_bool(request.data.get("looking_for_team"))
        game_id = request.data.get("game_id") or request.data.get("game")

        if ign is not None:
            profile.ign = ign
        if experience is not None and str(experience).isdigit():
            profile.experience = int(experience)
        if looking_for_team is not None:
            profile.looking_for_team = looking_for_team
        if game_id and str(game_id).isdigit():
            profile.game = Game.objects.get(id=int(game_id))

        if "featured_image" in request.FILES:
            profile.featured_image = request.FILES["featured_image"]

        if "roles" in request.data:
            roles = _parse_roles(request.data.get("roles"))
            profile.roles.set(Role.objects.filter(id__in=roles))
        profile.save()

        serializer = UserGameProfileSerializer(profile, context={'request': request})
        return Response({"msg": "updated", "profile": serializer.data}, status=status.HTTP_200_OK)


class TeamProfileDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        team = Team.objects.filter(created_by=request.user).select_related('game').prefetch_related('roles_needed').first()
        if not team:
            return Response({"msg": "fetched", "team": None}, status=status.HTTP_200_OK)

        serializer = TeamProfileSerializer(team, context={'request': request})
        return Response({"msg": "fetched", "team": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        existing = Team.objects.filter(created_by=request.user).first()
        if existing:
            return Response({"msg": "Team already exists"}, status=status.HTTP_400_BAD_REQUEST)

        name = request.data.get("name")
        if not name:
            return Response({"msg": "Team name is required"}, status=status.HTTP_400_BAD_REQUEST)

        game_id = request.data.get("game_id") or request.data.get("game")
        game = Game.objects.get(id=int(game_id)) if game_id and str(game_id).isdigit() else None

        team = Team.objects.create(
            name=name,
            created_by=request.user,
            description=request.data.get("description", ""),
            game=game,
            location=request.data.get("location", ""),
            looking_for_players=_parse_bool(request.data.get("looking_for_players")) or False,
            logo=request.FILES.get("logo"),
        )

        if "roles_needed" in request.data:
            roles = _parse_roles(request.data.get("roles_needed"))
            team.roles_needed.set(Role.objects.filter(id__in=roles))

        serializer = TeamProfileSerializer(team, context={'request': request})
        return Response({"msg": "created", "team": serializer.data}, status=status.HTTP_201_CREATED)

    def patch(self, request):
        team = Team.objects.filter(created_by=request.user).select_related('game').prefetch_related('roles_needed').first()
        if not team:
            return Response({"msg": "Team not found"}, status=status.HTTP_404_NOT_FOUND)

        name = request.data.get("name")
        if name is not None:
            team.name = name
        description = request.data.get("description")
        if description is not None:
            team.description = description
        location = request.data.get("location")
        if location is not None:
            team.location = location
        looking_for_players = _parse_bool(request.data.get("looking_for_players"))
        if looking_for_players is not None:
            team.looking_for_players = looking_for_players
        game_id = request.data.get("game_id") or request.data.get("game")
        if game_id and str(game_id).isdigit():
            team.game = Game.objects.get(id=int(game_id))
        if "logo" in request.FILES:
            team.logo = request.FILES["logo"]

        roles = _parse_roles(request.data.get("roles_needed"))
        if roles:
            team.roles_needed.set(Role.objects.filter(id__in=roles))

        team.save()
        serializer = TeamProfileSerializer(team, context={'request': request})
        return Response({"msg": "updated", "team": serializer.data}, status=status.HTTP_200_OK)


class PasswordResetRequest(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"msg": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
            send_mail(
                "Reset your password",
                f"Use the link to reset your password: {reset_url}",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,
            )

        return Response({"msg": "If the account exists, a reset link has been sent."}, status=status.HTTP_200_OK)


class PasswordResetConfirm(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not uid or not token or not new_password:
            return Response({"msg": "uid, token, and new_password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except Exception:
            return Response({"msg": "Invalid reset link"}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"msg": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"msg": "Password updated successfully"}, status=status.HTTP_200_OK)
