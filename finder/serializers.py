from rest_framework import serializers
from .models import RecruitmentPost, RecruitmentApplication, TeamInvitation


class RecruitmentPostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecruitmentPost
        fields = ['uuid', 'team', 'created_by', 'title', 'description', 'roles', 'created_at']


class RecruitmentPostSerializer(serializers.ModelSerializer):
    team_logo = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()
    team_game = serializers.SerializerMethodField()
    team_location = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()

    class Meta:
        model = RecruitmentPost
        fields = ['uuid', 'team_logo', 'team_name', 'team_game', 'team_location', 'created_by', 'title', 'description', 'roles', 'created_at']
    def get_team_logo(self, obj):
        return obj.team.logo.url if obj.team.logo else None
    def get_team_name(self, obj):
        return obj.team.name
    def get_team_game(self, obj):
        return obj.team.game.name
    def get_team_location(self, obj):
        return obj.team.location
    def get_roles(self, obj):
        return [role.name for role in obj.roles.all()]

class RecruitmentApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecruitmentApplication
        fields = ['uuid', 'recruitment_post', 'applicant', 'message', 'created_at', 'status']

class TeamInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamInvitation
        fields = ['uuid', 'team', 'player', 'message', 'created_at', 'status']
