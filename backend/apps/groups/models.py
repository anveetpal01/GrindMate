"""Friend group + invite + membership models.

A Group is a small (≤ ~50 user) cohort. Membership is a through model so
we can attach role + joined_at metadata. Invites are tokenized links.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone


class Group(models.Model):
    """A cohort of grinding friends."""

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    name = models.CharField(max_length=80, validators=[MinLengthValidator(3)])
    description = models.TextField(blank=True, max_length=500)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_groups",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="GroupMembership",
        related_name="grindmate_groups",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.name

    def has_member(self, user) -> bool:
        return self.memberships.filter(user=user).exists()

    def is_admin(self, user) -> bool:
        return self.memberships.filter(user=user, role=GroupMembership.ROLE_ADMIN).exists()


class GroupMembership(models.Model):
    """Through-table for Group ↔ User M2M, with role + join time."""

    ROLE_ADMIN = "admin"
    ROLE_MEMBER = "member"
    ROLE_CHOICES = ((ROLE_ADMIN, "Admin"), (ROLE_MEMBER, "Member"))

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(max_length=8, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["group", "user"], name="unique_group_user"),
        ]
        indexes = [models.Index(fields=["user", "group"])]

    def __str__(self) -> str:
        return f"{self.user.username} in {self.group.name} ({self.role})"


class GroupInvite(models.Model):
    """Single-use-or-multi-use invite token to join a group."""

    DEFAULT_EXPIRY_HOURS = 24 * 7  # 7 days

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="invites")
    token = models.CharField(
        max_length=64,
        unique=True,
        default=secrets.token_urlsafe,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="group_invites_created",
    )
    expires_at = models.DateTimeField()
    max_uses = models.PositiveIntegerField(null=True, blank=True)  # null = unlimited
    use_count = models.PositiveIntegerField(default=0)
    revoked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["token"])]

    def __str__(self) -> str:
        return f"invite for {self.group.name} ({self.token[:8]}…)"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=self.DEFAULT_EXPIRY_HOURS)
        super().save(*args, **kwargs)

    def is_active(self) -> bool:
        if self.revoked:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return not (self.max_uses is not None and self.use_count >= self.max_uses)

    def consume(self) -> None:
        self.use_count = models.F("use_count") + 1
        self.save(update_fields=["use_count"])
        self.refresh_from_db(fields=["use_count"])
