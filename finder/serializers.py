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
    applied = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = RecruitmentPost
        fields = ['id', 'uuid', 'team_logo', 'team_name', 'team_game', 'team_location', 'applied', 'created_by', 'title', 'description', 'roles', 'created_at']
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
    def get_applied(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return RecruitmentApplication.objects.filter(recruitment_post=obj, applicant=user).exists()
        return False


class RecruitmentApplicationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = RecruitmentApplication
        fields = ['uuid', 'recruitment_post', 'applicant', 'message', 'created_at', 'status']
        read_only_fields = ['applicant']
    

class TeamInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamInvitation
        fields = ['uuid', 'team', 'player', 'message', 'created_at', 'status']
