from typing import Any, Dict, Optional, Type, TypeVar
from django.contrib.auth.models import update_last_login
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from rest_framework_simplejwt.settings import api_settings
from accounts.models import Role, Team, UserGameProfile
from games.models import Game
User = get_user_model()

def get_json_default():
    return {}

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
    game = serializers.PrimaryKeyRelatedField(queryset=Game.objects.all())
    ign = serializers.CharField(max_length=25)
    game_data = serializers.JSONField(default=get_json_default)
    preference_data = serializers.JSONField(default=get_json_default)
    class Meta:
        model = User
        fields = ['name', 'email', 'password', 'location', 'ign', 'game', 'roles', 'game_data', 'preference_data']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        roles = validated_data.pop('roles', [])
        game = validated_data.pop('game', None)
        ign = validated_data.pop('ign', None)
        game_data = validated_data.pop('game_data', {})
        preference_data = validated_data.pop('preference_data', {})
        user = User.objects.create_user(**validated_data)
        # Add game profile
        ugp = UserGameProfile.objects.create(
            user=user,
            ign=ign,
            game=game,
            game_data=game_data,
            preference_data=preference_data,
        )
        ugp.roles.set(roles)
        return user

class TeamSignupSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(max_length=150, write_only=True)
    logo = serializers.ImageField(required=False, write_only=True)
    looking_for_players = serializers.IntegerField(default=0, write_only=True)
    looking_for_roles = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), many=True, required=False, write_only=True)
    game = serializers.PrimaryKeyRelatedField(queryset=Game.objects.all())

    class Meta:
        model = User
        fields = ['name', 'email', 'password', 'location', 'team_name', 'logo', 'looking_for_players', 'looking_for_roles', 'game']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        game = validated_data.pop("game")
        team_name = validated_data.pop('team_name')
        logo = validated_data.pop('logo', None)
        looking_for_players = validated_data.pop('looking_for_players', 0)
        looking_for_roles = validated_data.pop('looking_for_roles', [])

        # Create the User
        user = User.objects.create_user(**validated_data)

        # Create the Team
        team = Team.objects.create(
            name=team_name,
            created_by=user,
            logo=logo,
            game=game,
            location=validated_data.get('location', ''),
            looking_for_players=looking_for_players,
        )
        team.looking_for_roles.set(looking_for_roles)
        team.save()
        user.save()

        return user
