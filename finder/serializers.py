from rest_framework import serializers
from accounts.models import Team


class TeamSearchSerializer(serializers.ModelSerializer):
    team_logo = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()
    team_game = serializers.SerializerMethodField()
    team_location = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(source="created_by.id", read_only=True)

    class Meta:
        model = Team
        fields = [
            'id',
            'team_logo',
            'team_name',
            'team_game',
            'team_location',
            'description',
            'roles',
            'looking_for_players',
            'owner_id',
        ]

    def get_team_logo(self, obj):
        if not obj.logo:
            return None
        request = self.context.get('request')
        url = obj.logo.url
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_team_name(self, obj):
        return obj.name

    def get_team_game(self, obj):
        return obj.game.name if obj.game else None

    def get_team_location(self, obj):
        return obj.location

    def get_roles(self, obj):
        return [role.name for role in obj.roles_needed.all()]
