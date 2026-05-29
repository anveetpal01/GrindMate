"""LeetCode integration models.

LeetCodeAccount links one user to one LeetCode handle. Problem caches the
public catalog of LeetCode problems. SubmissionLog records each accepted
submission a user has - the (user, solved_at) composite index supports
the leaderboard's "this week" / streak queries.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from .managers import SubmissionLogManager


class SyncStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    OK = "ok", "OK"
    FAILED = "failed", "Failed"
    UNVERIFIED = "unverified", "Unverified"


class Difficulty(models.TextChoices):
    EASY = "easy", "Easy"
    MEDIUM = "medium", "Medium"
    HARD = "hard", "Hard"


class LeetCodeAccount(models.Model):
    """A user's linked LeetCode handle. One per user (OneToOne)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="leetcode_account",
    )
    handle = models.CharField(
        max_length=64,
        unique=True,
        help_text="LeetCode username (case-insensitive).",
    )

    # Sync state
    sync_status = models.CharField(
        max_length=16,
        choices=SyncStatus.choices,
        default=SyncStatus.UNVERIFIED,
    )
    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_sync_error = models.TextField(blank=True)

    # Cached aggregates - refreshed on every successful sync.
    total_solved = models.PositiveIntegerField(default=0)
    easy_solved = models.PositiveIntegerField(default=0)
    medium_solved = models.PositiveIntegerField(default=0)
    hard_solved = models.PositiveIntegerField(default=0)
    ranking = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "LeetCode account"

    def __str__(self) -> str:
        return f"{self.user.username} → {self.handle}"

    @property
    def is_verified(self) -> bool:
        return self.sync_status != SyncStatus.UNVERIFIED


class Problem(models.Model):
    """Cached LeetCode problem record. Populated on demand as we see new slugs."""

    title_slug = models.SlugField(max_length=128, unique=True)
    title = models.CharField(max_length=256)
    difficulty = models.CharField(max_length=8, choices=Difficulty.choices)
    topic_tags = models.JSONField(default=list, blank=True)
    is_premium = models.BooleanField(default=False)
    leetcode_id = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("title_slug",)
        indexes = [models.Index(fields=["difficulty"])]

    def __str__(self) -> str:
        return self.title


class SubmissionLog(models.Model):
    """One row per accepted submission of a problem by a user.

    Sync source: 'auto' (LeetCode GraphQL pull) or 'manual' (user marked it).
    Composite index on (user, solved_at) is what the leaderboard queries hit.
    """

    SOURCE_AUTO = "auto"
    SOURCE_MANUAL = "manual"
    SOURCE_CHOICES = ((SOURCE_AUTO, "Auto"), (SOURCE_MANUAL, "Manual"))

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    problem = models.ForeignKey(
        Problem,
        on_delete=models.PROTECT,
        related_name="submissions",
    )
    solved_at = models.DateTimeField()
    source = models.CharField(max_length=8, choices=SOURCE_CHOICES, default=SOURCE_AUTO)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = SubmissionLogManager()

    class Meta:
        ordering = ("-solved_at",)
        indexes = [
            models.Index(fields=["user", "-solved_at"], name="submission_user_date_idx"),
            models.Index(fields=["solved_at"]),
        ]
        constraints = [
            # A user solving the same problem twice in the same minute is a
            # duplicate sync, not a new event.
            models.UniqueConstraint(
                fields=["user", "problem", "solved_at"],
                name="unique_user_problem_solved_at",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} solved {self.problem.title_slug} @ {self.solved_at:%Y-%m-%d}"
