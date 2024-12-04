# views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import RecruitmentPost, RecruitmentApplication, PlayerRecruitmentPost, TeamInvitation
from .serializers import RecruitmentPostSerializer, RecruitmentApplicationSerializer, PlayerRecruitmentPostSerializer, TeamInvitationSerializer


class RecruitmentPostListCreateView(generics.ListCreateAPIView):
    queryset = RecruitmentPost.objects.all()
    serializer_class = RecruitmentPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        print(self.request.user)
        serializer.save(created_by=self.request.user)

class RecruitmentApplicationListCreateView(generics.ListCreateAPIView):
    queryset = RecruitmentApplication.objects.all()
    serializer_class = RecruitmentApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user)

class PlayerRecruitmentPostListCreateView(generics.ListCreateAPIView):
    queryset = PlayerRecruitmentPost.objects.all()
    serializer_class = PlayerRecruitmentPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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
