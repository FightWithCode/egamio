import uuid
from django.db import models
from django.conf import settings

from accounts.models import Team, Role
# Assuming you have the Role and Team models as shown previously

class RecruitmentPost(models.Model):
    """
    Model representing a recruitment post created by a team owner to recruit players.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='recruitment_posts')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    roles = models.ManyToManyField(Role, related_name='recruitment_posts', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.team.name}"


class RecruitmentApplication(models.Model):
    """
    Model representing a player's application to a recruitment post.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    recruitment_post = models.ForeignKey(RecruitmentPost, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="player_applications")
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending')

    def __str__(self):
        return f"Application by {self.applicant.name} for {self.recruitment_post.title}"


class PlayerRecruitmentPost(models.Model):
    """
    Model representing a post created by a player looking for a team.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='player_recruitment_posts')
    title = models.CharField(max_length=100)
    description = models.TextField()
    roles = models.ManyToManyField(Role, related_name='player_recruitment_posts', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.user.name}"


class TeamInvitation(models.Model):
    """
    Model representing an invitation sent by a team owner to a player.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='invitations')
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invitations')
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending')

    def __str__(self):
        return f"Invitation from {self.team.name} to {self.player.name}"
