from django.db import models
from django.utils.translation import gettext_lazy as _
# models import
from egamio.utils import TimeStamp


class Game(models.Model, TimeStamp):
    """
    A model representing a Game.
    """
    name = models.CharField(_("game name"), max_length=150, unique=True)
    logo = models.ImageField(_("logo"), upload_to='game_logos/', blank=True, null=True)
    genre = models.CharField(_("genre"), max_length=100, blank=True)
    description = models.TextField(_("description"), blank=True)
    
    # Timestamp fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("game")
        verbose_name_plural = _("games")

    def __str__(self):
        return self.name


class GameTag(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='thread_tags')
    name = models.CharField(_("tag name"), max_length=50)
    usage_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-usage_count', 'name']
        unique_together = ('game', 'name')
        indexes = [
            models.Index(fields=['game', 'name']),
            models.Index(fields=['game', 'usage_count']),
        ]

    def __str__(self):
        return f'{self.game.name}: {self.name}'
