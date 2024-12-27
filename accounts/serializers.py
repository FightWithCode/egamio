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


class UserGameProfileSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    game_name = serializers.CharField(source='game.name', read_only=True)
    roles_list = serializers.SerializerMethodField()

    class Meta:
        model = UserGameProfile
        fields = ['uuid', 'user_name', 'ign', 'game_name', 'roles_list', 'featured_image', 'experience']

    def get_roles_list(self, obj):
        return [role.name for role in obj.roles.all()]


class TeamSerializer(serializers.ModelSerializer):
    game_name = serializers.CharField(source='game.name', read_only=True)
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'logo', 'game_name', 
                 'location', 'looking_for_players']


class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'location']