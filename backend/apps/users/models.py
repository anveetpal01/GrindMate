"""User domain models.

The custom User uses email as the auth field but keeps a public username
that other users see in groups and on profile pages.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone as django_tz
from django.utils.translation import gettext_lazy as _

from .managers import UserManager

USERNAME_REGEX = RegexValidator(
    regex=r"^[a-zA-Z0-9_]{3,30}$",
    message=_("Username must be 3-30 characters: letters, digits, underscores."),
)


class User(AbstractBaseUser, PermissionsMixin):
    """Application user.

    `email` authenticates; `username` is the public handle shown in groups.
    """

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    email = models.EmailField(_("email address"), unique=True)
    username = models.CharField(
        _("username"),
        max_length=30,
        unique=True,
        validators=[USERNAME_REGEX],
        help_text=_("Public handle. 3-30 chars: letters, digits, underscores."),
    )
    display_name = models.CharField(_("display name"), max_length=80, blank=True)
    avatar_url = models.URLField(_("avatar URL"), blank=True)
    timezone = models.CharField(_("timezone"), max_length=64, default="Asia/Kolkata")

    is_email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=django_tz.now)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ("-date_joined",)
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self) -> str:
        return self.username or self.email

    @property
    def name(self) -> str:
        return self.display_name or self.username

    def delete(self, *args, **kwargs):
        """Reassign or delete owned Groups before delete, since Group.owner
        is PROTECT and would otherwise block the cascade.

        Strategy per owned group:
          1. Transfer to the oldest other admin member, if any.
          2. Else promote the oldest other member to admin and transfer.
          3. Else (sole member) delete the group entirely.
        """
        import logging

        from apps.groups.models import GroupMembership

        log = logging.getLogger(__name__)
        for group in list(self.owned_groups.all()):
            replacement = (
                group.memberships.exclude(user=self)
                .filter(role=GroupMembership.ROLE_ADMIN)
                .order_by("joined_at")
                .first()
            )
            if replacement is None:
                replacement = group.memberships.exclude(user=self).order_by("joined_at").first()
                if replacement is not None:
                    replacement.role = GroupMembership.ROLE_ADMIN
                    replacement.save(update_fields=["role"])

            if replacement is None:
                log.info("Deleting orphan group_id=%s on owner delete", group.id)
                group.delete()
                continue

            group.owner = replacement.user
            group.save(update_fields=["owner"])
            log.info(
                "Transferred group_id=%s ownership user_id=%s -> user_id=%s",
                group.id,
                self.id,
                replacement.user_id,
            )

        return super().delete(*args, **kwargs)


class EmailVerificationToken(models.Model):
    """Single-use signup verification token. Expires after 24h."""

    EXPIRY = timedelta(hours=24)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )
    token = models.CharField(max_length=64, unique=True, default=secrets.token_urlsafe)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["token"])]

    def __str__(self) -> str:
        return f"token for {self.user.username} ({self.token[:8]}…)"

    def is_expired(self) -> bool:
        return django_tz.now() > self.created_at + self.EXPIRY

    def is_usable(self) -> bool:
        return self.used_at is None and not self.is_expired()

    def consume(self) -> None:
        self.used_at = django_tz.now()
        self.save(update_fields=["used_at"])


class PasswordResetToken(models.Model):
    """Single-use password reset token. Expires after 1h (shorter than verify
    because it lets an attacker change the password)."""

    EXPIRY = timedelta(hours=1)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token = models.CharField(max_length=64, unique=True, default=secrets.token_urlsafe)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["token"])]

    def __str__(self) -> str:
        return f"reset token for {self.user.username} ({self.token[:8]})"

    def is_expired(self) -> bool:
        return django_tz.now() > self.created_at + self.EXPIRY

    def is_usable(self) -> bool:
        return self.used_at is None and not self.is_expired()

    def consume(self) -> None:
        self.used_at = django_tz.now()
        self.save(update_fields=["used_at"])
