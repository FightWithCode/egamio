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
