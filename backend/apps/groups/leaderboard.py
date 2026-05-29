"""Group leaderboard query.

Single annotated query computes per-member solve counts and difficulty-weighted
scores in the database; select_related avoids N+1 on user joins. Streak is
computed in Python from a prefetched per-user date list.

Result is cached for LEADERBOARD_CACHE_TTL seconds, keyed by
(group_public_id, period), and invalidated on each new SubmissionLog.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from django.core.cache import cache
from django.db.models import Case, Count, IntegerField, Q, Sum, Value, When
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from apps.leetcode.managers import compute_streaks
from apps.leetcode.models import SubmissionLog

Period = Literal["daily", "weekly", "all-time"]
LEADERBOARD_CACHE_TTL = 60  # seconds - leaderboards refresh on user action

# Difficulty weights - easy/medium/hard mapped to 1/3/5 points.
EASY_WEIGHT, MEDIUM_WEIGHT, HARD_WEIGHT = 1, 3, 5


@dataclass(frozen=True)
class LeaderboardRow:
    rank: int
    user_id: int
    public_id: str
    username: str
    display_name: str
    avatar_url: str
    total_solved: int
    easy_solved: int
    medium_solved: int
    hard_solved: int
    score: int
    current_streak: int
    longest_streak: int


def _period_window(period: Period) -> tuple[datetime, datetime] | tuple[None, None]:
    now = timezone.localtime()
    if period == "daily":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, start + timedelta(days=1)
    if period == "weekly":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, start + timedelta(days=7)
    # all-time: no window
    return None, None


def _cache_key(group_public_id: str, period: Period) -> str:
    return f"leaderboard:{group_public_id}:{period}"


def invalidate_group_leaderboard(group_public_id: str) -> None:
    """Drop all cached periods for this group - call after a member's sync."""
    for period in ("daily", "weekly", "all-time"):
        cache.delete(_cache_key(group_public_id, period))


def compute_leaderboard(group, period: Period = "weekly") -> list[LeaderboardRow]:
    """Return the leaderboard rows for `group` and `period`, cached."""
    key = _cache_key(str(group.public_id), period)
    hit = cache.get(key)
    if hit is not None:
        return hit

    rows = _compute_uncached(group, period)
    cache.set(key, rows, timeout=LEADERBOARD_CACHE_TTL)
    return rows


def _compute_uncached(group, period: Period) -> list[LeaderboardRow]:
    start, end = _period_window(period)

    # Build the period filter once and reuse in every annotation. We're
    # counting through GroupMembership → user → submissions, so all keys
    # must walk that path.
    if start is not None:
        scope = Q(
            user__submissions__solved_at__gte=start,
            user__submissions__solved_at__lt=end,
        )
    else:
        scope = Q()

    # Single SQL: pull each member with annotated counts. select_related avoids
    # a per-row user lookup; values_list at the end pulls everything we need.
    members_qs = (
        group.memberships.select_related("user")
        .annotate(
            total=Coalesce(Count("user__submissions", filter=scope, distinct=True), Value(0)),
            easy=Coalesce(
                Count(
                    "user__submissions",
                    filter=scope & Q(user__submissions__problem__difficulty="easy"),
                    distinct=True,
                ),
                Value(0),
            ),
            medium=Coalesce(
                Count(
                    "user__submissions",
                    filter=scope & Q(user__submissions__problem__difficulty="medium"),
                    distinct=True,
                ),
                Value(0),
            ),
            hard=Coalesce(
                Count(
                    "user__submissions",
                    filter=scope & Q(user__submissions__problem__difficulty="hard"),
                    distinct=True,
                ),
                Value(0),
            ),
            score=Coalesce(
                Sum(
                    Case(
                        When(
                            user__submissions__problem__difficulty="easy", then=Value(EASY_WEIGHT)
                        ),
                        When(
                            user__submissions__problem__difficulty="medium",
                            then=Value(MEDIUM_WEIGHT),
                        ),
                        When(
                            user__submissions__problem__difficulty="hard", then=Value(HARD_WEIGHT)
                        ),
                        default=Value(0),
                        output_field=IntegerField(),
                    ),
                    filter=scope,
                ),
                Value(0),
            ),
        )
        .order_by("-score", "-total", "user__username")
    )

    user_ids = [m.user_id for m in members_qs]

    # Streaks - fetched in one pass over all members' distinct dates.
    distinct_dates = (
        SubmissionLog.objects.filter(user_id__in=user_ids)
        .annotate(d=TruncDate("solved_at"))
        .values_list("user_id", "d")
        .distinct()
        .order_by("-d")
    )

    user_dates: dict[int, list] = {}
    for user_id, d in distinct_dates:
        user_dates.setdefault(user_id, []).append(d)

    rows: list[LeaderboardRow] = []
    for rank, m in enumerate(members_qs, start=1):
        current, longest = compute_streaks(user_dates.get(m.user_id, []))
        rows.append(
            LeaderboardRow(
                rank=rank,
                user_id=m.user_id,
                public_id=str(m.user.public_id),
                username=m.user.username,
                display_name=m.user.display_name or m.user.username,
                avatar_url=m.user.avatar_url,
                total_solved=m.total,
                easy_solved=m.easy,
                medium_solved=m.medium,
                hard_solved=m.hard,
                score=m.score,
                current_streak=current,
                longest_streak=longest,
            ),
        )

    return rows
