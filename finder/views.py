# views.py
import json
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from .serializers import TeamSearchSerializer
from accounts.models import UserGameProfile, Team
from accounts.serializers import UserGameProfileSerializer



def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


class PlayerSearchPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'

class PlayerSearchAPIView(generics.ListAPIView):
    serializer_class = UserGameProfileSerializer
    pagination_class = PlayerSearchPagination

    def get_queryset(self):
        queryset = UserGameProfile.objects.select_related('user', 'game').prefetch_related('roles')

        game = self.request.query_params.get('game', None)
        role = self.request.query_params.get('role', None)
        ign = self.request.query_params.get('ign', None)
        game_data = self.request.query_params.get('game_data', None)
        looking_for = _parse_bool(self.request.query_params.get('looking_for', None))

        filters = Q()
        if game:
            filters &= Q(game__name__icontains=game)
        if role:
            filters &= Q(roles__name__iexact=role)
        if ign:
            filters &= Q(ign__icontains=ign)
        if looking_for is True:
            filters &= Q(looking_for_team=True)
        if game_data:
            try:
                game_data_dict = json.loads(game_data)
                filters &= Q(game_data__contains=game_data_dict)
            except json.JSONDecodeError:
                pass

        if filters:
            queryset = queryset.filter(filters).distinct()

        return queryset

class TeamSearchAPIView(generics.ListAPIView):
    serializer_class = TeamSearchSerializer
    pagination_class = PlayerSearchPagination
    
    def get_queryset(self):
        queryset = Team.objects.select_related('game', 'created_by').prefetch_related('roles_needed').all().order_by('-id')
        
        # Get query parameters
        team_name = self.request.query_params.get('team_name', None)
        location = self.request.query_params.get('location', None)
        game_name = self.request.query_params.get('game_name', None)
        roles = self.request.query_params.get('roles', None)
        looking_for = _parse_bool(self.request.query_params.get('looking_for', None))

        filters = Q()
        if team_name:
            filters &= Q(name__icontains=team_name)
        
        if location:
            filters &= Q(location__icontains=location)
        
        if game_name:
            filters &= Q(game__name__icontains=game_name)
        
        if roles:
            roles_list = [role.strip() for role in roles.split(',') if role.strip()]
            if roles_list:
                filters &= Q(roles_needed__name__in=roles_list)

        if looking_for is True:
            filters &= Q(looking_for_players=True)

        if filters:
            queryset = queryset.filter(filters).distinct()
        return queryset


class UpdatePlayerAvailability(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        looking_for_team = _parse_bool(request.data.get("looking_for_team"))
        if looking_for_team is None:
            return Response({"msg": "looking_for_team is required"}, status=status.HTTP_400_BAD_REQUEST)

        profile = UserGameProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({"msg": "Player profile not found"}, status=status.HTTP_404_NOT_FOUND)

        profile.looking_for_team = looking_for_team
        profile.save(update_fields=["looking_for_team"])
        return Response({"msg": "updated", "looking_for_team": profile.looking_for_team}, status=status.HTTP_200_OK)


class UpdateTeamAvailability(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        looking_for_players = _parse_bool(request.data.get("looking_for_players"))
        if looking_for_players is None:
            return Response({"msg": "looking_for_players is required"}, status=status.HTTP_400_BAD_REQUEST)

        team = Team.objects.filter(created_by=request.user).first()
        if not team:
            return Response({"msg": "Team not found"}, status=status.HTTP_404_NOT_FOUND)

        team.looking_for_players = looking_for_players
        team.save(update_fields=["looking_for_players"])
        return Response({"msg": "updated", "looking_for_players": team.looking_for_players}, status=status.HTTP_200_OK)
