from django.db import models
from django.core.mail import send_mail
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .managers import UserManager

# model imports
from egamio.utils import TimeStamp


class Role(models.Model):
    """
    Model representing a role.
    """
    name = models.CharField(_("role name"), max_length=150, unique=True)
    game = models.ForeignKey(
        'games.Game', 
        on_delete=models.CASCADE, 
        related_name='roles', 
        verbose_name=_("game")
    )
    description = models.TextField(_("role description"), blank=True)

    def __str__(self):
        return self.name


class Team(models.Model, TimeStamp):
    """
    A model representing a Team.
    """
    name = models.CharField(_("team name"), max_length=150, unique=True)
    description = models.TextField(_("description"), blank=True)
    logo = models.ImageField(_("logo"), upload_to='team_logos/', blank=True, null=True)
    game = models.ForeignKey(
        'games.Game', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='teams', 
        verbose_name=_("game")
    )
    location = models.CharField(max_length=255, blank=True, null=True)
    looking_for_players = models.IntegerField(default=0)
    looking_for_roles = models.ManyToManyField(Role, related_name='looking_for_roles', blank=True)


    class Meta:
        verbose_name = _("team")
        verbose_name_plural = _("teams")

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.

    Email and password are required. Other fields are optional.
    """
    name = models.CharField(_("first name"), max_length=150, blank=True)
    email = models.EmailField(_("email address"), unique=True)
    game = models.ForeignKey(
        'games.Game',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_("game")
    )
    roles = models.ManyToManyField(Role, related_name='users', blank=True)
    location = models.CharField(max_length=150, default=None, null=True, blank=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        verbose_name=_("team")
    )
    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        return self.name

    def get_short_name(self):
        """Return the short name for the user."""
        return self.name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

