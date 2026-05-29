"""Custom managers / querysets for the leetcode app.

Encapsulating "this week" / "by difficulty" / streak queries here keeps
views and Celery tasks free of ORM noise and makes them reusable.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from itertools import pairwise
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import Count, Q
from django.utils import timezone

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser


class SubmissionLogQuerySet(models.QuerySet):
    def for_user(self, user: AbstractBaseUser) -> SubmissionLogQuerySet:
        return self.filter(user=user)

    def in_range(self, start: datetime, end: datetime) -> SubmissionLogQuerySet:
        return self.filter(solved_at__gte=start, solved_at__lt=end)

    def today(self) -> SubmissionLogQuerySet:
        now = timezone.localtime()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return self.in_range(start, start + timedelta(days=1))

    def this_week(self) -> SubmissionLogQuerySet:
        """Monday-to-Monday window in the local timezone."""
        now = timezone.localtime()
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        return self.in_range(start, start + timedelta(days=7))

    def by_difficulty(self) -> dict[str, int]:
        """Return a {difficulty: count} dict - useful on profile pages."""
        rows = (
            self.values("problem__difficulty")
            .annotate(n=Count("id"))
            .values_list("problem__difficulty", "n")
        )
        return dict(rows)

    def distinct_solved_dates(self, user: AbstractBaseUser) -> list[date]:
        """List of unique local dates (descending) the user has a solve on.

        Used by the streak calculator and heatmap.
        """
        return list(
            self.for_user(user)
            .annotate(d=models.functions.TruncDate("solved_at"))
            .values_list("d", flat=True)
            .distinct()
            .order_by("-d"),
        )


class SubmissionLogManager(models.Manager.from_queryset(SubmissionLogQuerySet)):
    def get_queryset(self) -> SubmissionLogQuerySet:  # type: ignore[override]
        return SubmissionLogQuerySet(self.model, using=self._db)


def compute_streaks(distinct_dates: list[date]) -> tuple[int, int]:
    """Given a list of distinct local solve-dates (descending), return
    (current_streak, longest_streak)."""
    if not distinct_dates:
        return 0, 0

    today = timezone.localdate()
    sorted_desc = sorted(set(distinct_dates), reverse=True)

    # Current streak - only counts if user solved today or yesterday.
    current = 0
    expected = today
    for d in sorted_desc:
        if d == expected:
            current += 1
            expected = expected - timedelta(days=1)
        elif d == expected - timedelta(days=1) and current == 0:
            # First date is yesterday - streak still alive (today not over).
            current = 1
            expected = d - timedelta(days=1)
        else:
            break

    # Longest streak - scan ascending.
    sorted_asc = sorted(set(distinct_dates))
    longest = run = 1
    for prev, curr in pairwise(sorted_asc):
        if curr - prev == timedelta(days=1):
            run += 1
            longest = max(longest, run)
        else:
            run = 1
    return current, longest


__all__ = ["SubmissionLogQuerySet", "SubmissionLogManager", "compute_streaks", "Q"]
