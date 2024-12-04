import os
from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import Response
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserGameProfile, Team, Role
from games.models import Game
from .serializers import PlayerSignupSerializer, TeamSignupSerializer, CustomTokenObtainPairSerializer


User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response = response.data
        response["msg"] = "Success"
        return Response(response, status=status.HTTP_200_OK)

class CustomTokenRefreshView(TokenRefreshView):
    pass



class PlayerSignupView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = PlayerSignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "Player signup successful"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TeamSignupView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = TeamSignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "Team signup successful"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleSignInView(APIView):
    def post(self, request):
        try:
            # Verify the Google token
            google_token = request.data.get('credential')
            idinfo = id_token.verify_oauth2_token(
                google_token, 
                requests.Request(), 
                settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["client_id"]
            )
            print(idinfo)
            email = idinfo['email']
            name = idinfo.get('name', '')
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    name=name,
                    email=email,
                )

            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'id': user.id,
                'full_name': user.get_full_name(),
            })

        except ValueError as e:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
                looking_for_players = request.data.get('looking_for_players', 0)
                looking_for_roles = Role.objects.filter(id__in=request.data.get('looking_for_roles', []))

                # Create the Team
                team = Team.objects.create(
                    name=team_name,
                    created_by=request.user,
                    logo=logo,
                    game=game,
                    location=request.data.get('location', ''),
                    looking_for_players=looking_for_players,
                )
                team.looking_for_roles.set(looking_for_roles)
                team.save()
                request.user.save()
                return Response({"msg": "Team signup successful"}, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({'msg': "Something went wrong!", 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
