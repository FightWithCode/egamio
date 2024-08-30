from rest_framework import serializers
from .models import RecruitmentPost, RecruitmentApplication, PlayerRecruitmentPost, TeamInvitation

class RecruitmentPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecruitmentPost
        fields = ['uuid', 'team', 'created_by', 'title', 'description', 'roles', 'created_at']

class RecruitmentApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecruitmentApplication
        fields = ['uuid', 'recruitment_post', 'applicant', 'message', 'created_at', 'status']

class PlayerRecruitmentPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerRecruitmentPost
        fields = ['uuid', 'user', 'title', 'description', 'roles', 'created_at']

class TeamInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamInvitation
        fields = ['uuid', 'team', 'player', 'message', 'created_at', 'status']
