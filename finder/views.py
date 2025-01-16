# views.py
import json
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import RecruitmentPost, RecruitmentApplication, TeamInvitation
from .serializers import RecruitmentPostSerializer, RecruitmentApplicationSerializer, TeamInvitationSerializer, RecruitmentPostCreateSerializer
from accounts.models import UserGameProfile, Team
from accounts.serializers import UserGameProfileSerializer



class RecruitmentPostListCreateView(generics.ListCreateAPIView):
    queryset = RecruitmentPost.objects.all()
    serializer_class = RecruitmentPostCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class RecruitmentApplicationListCreateView(generics.ListCreateAPIView):
    queryset = RecruitmentApplication.objects.all()
    serializer_class = RecruitmentApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user)


class TeamInvitationListCreateView(generics.ListCreateAPIView):
    queryset = TeamInvitation.objects.all()
    serializer_class = TeamInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

class RecruitmentApplicationUpdateView(generics.UpdateAPIView):
    queryset = RecruitmentApplication.objects.all()
    serializer_class = RecruitmentApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        application = self.get_object()
        if application.recruitment_post.created_by != request.user:
            return Response({"error": "Not authorized to update this application."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

class TeamInvitationUpdateView(generics.UpdateAPIView):
    queryset = TeamInvitation.objects.all()
    serializer_class = TeamInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        invitation = self.get_object()
        if invitation.team.created_by != request.user:
            return Response({"error": "Not authorized to update this invitation."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)


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

        filters = Q()
        if game:
            filters &= Q(game__name__icontains=game)
        if role:
            filters &= Q(roles__name__iexact=role)
        if ign:
            filters &= Q(ign__icontains=ign)
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
    serializer_class = RecruitmentPostSerializer
    pagination_class = PlayerSearchPagination
    
    def get_queryset(self):
        queryset = RecruitmentPost.objects.select_related('team', 'team__game', 'created_by').all().order_by('-id')
        
        # Get query parameters
        team_name = self.request.query_params.get('team_name', None)
        location = self.request.query_params.get('location', None)
        game_name = self.request.query_params.get('game_name', None)
        roles = self.request.query_params.get('roles', None)

        filters = Q()
        if team_name:
            filters &= Q(team__name__icontains=team_name)
        
        if location:
            filters &= Q(team__location__icontains=location)
        
        if game_name:
            filters &= Q(team__game__name__icontains=game_name)
        
        if roles:
            roles_list = roles.split(',')
            filters &= Q(roles__name__in=roles_list)

        if filters:
            queryset = queryset.filter(filters).distinct()
        return queryset
