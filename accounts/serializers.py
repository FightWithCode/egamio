from typing import Any, Dict, Optional, Type, TypeVar
from django.contrib.auth.models import update_last_login
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from rest_framework_simplejwt.settings import api_settings
from accounts.models import Role, Team
from games.models import Game
User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, str]:
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        data["id"] = self.user.id 
        data["full_name"] = self.user.get_full_name()
        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email')


class PlayerSignupSerializer(serializers.ModelSerializer):
    roles = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), many=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'password', 'location', 'roles']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        roles = validated_data.pop('roles', [])
        user = User.objects.create_user(**validated_data)
        user.roles.set(roles)
        return user

class TeamSignupSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(max_length=150, write_only=True)
    logo = serializers.ImageField(required=False, write_only=True)
    looking_for_players = serializers.IntegerField(default=0, write_only=True)
    looking_for_roles = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), many=True, required=False, write_only=True)
    roles = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), many=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'password', 'location', 'roles', 'team_name', 'logo', 'looking_for_players', 'looking_for_roles', 'game']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        game = validated_data.pop("game")
        team_name = validated_data.pop('team_name')
        logo = validated_data.pop('logo', None)
        looking_for_players = validated_data.pop('looking_for_players', 0)
        looking_for_roles = validated_data.pop('looking_for_roles', [])
        roles = validated_data.pop('roles', [])

        # Create the User
        user = User.objects.create_user(**validated_data)
        user.game = game
        user.roles.set(roles)

        # Create the Team
        team = Team.objects.create(
            name=team_name,
            logo=logo,
            game=game,
            location=validated_data.get('location', ''),
            looking_for_players=looking_for_players,
        )
        team.looking_for_roles.set(looking_for_roles)
        team.save()
        # Assign the User to the Team
        user.team = team
        user.save()

        return user
