"""Tests for SubmissionLog manager + streak helper."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time

from apps.leetcode.factories import ProblemFactory, SubmissionLogFactory
from apps.leetcode.managers import compute_streaks
from apps.leetcode.models import SubmissionLog
from apps.users.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def fixed_now():
    """Freeze 'now' on a Wednesday."""
    with freeze_time("2026-05-06 12:00:00") as frozen:  # Wednesday
        yield frozen


def test_today_filters_to_local_day(fixed_now):
    user = UserFactory()
    today_solve = SubmissionLogFactory(user=user, solved_at=timezone.now())
    SubmissionLogFactory(user=user, solved_at=timezone.now() - timedelta(days=2))

    qs = SubmissionLog.objects.for_user(user).today()
    assert list(qs) == [today_solve]


def test_this_week_returns_monday_to_monday(fixed_now):
    user = UserFactory()
    inside_week = SubmissionLogFactory(user=user, solved_at=timezone.now() - timedelta(days=2))
    outside_week = SubmissionLogFactory(user=user, solved_at=timezone.now() - timedelta(days=10))  # noqa: F841

    qs = SubmissionLog.objects.for_user(user).this_week()
    assert list(qs) == [inside_week]


def test_by_difficulty_returns_counts():
    user = UserFactory()
    SubmissionLogFactory.create_batch(2, user=user, problem=ProblemFactory(difficulty="easy"))
    SubmissionLogFactory(user=user, problem=ProblemFactory(difficulty="medium"))

    counts = SubmissionLog.objects.for_user(user).by_difficulty()
    assert counts == {"easy": 2, "medium": 1}


class TestComputeStreaks:
    def test_no_solves_returns_zeros(self):
        assert compute_streaks([]) == (0, 0)

    def test_single_solve_today_is_one(self):
        today = timezone.localdate()
        assert compute_streaks([today]) == (1, 1)

    def test_consecutive_streak(self):
        today = timezone.localdate()
        dates = [today, today - timedelta(days=1), today - timedelta(days=2)]
        current, longest = compute_streaks(dates)
        assert current == 3
        assert longest == 3

    def test_broken_streak_keeps_longest(self):
        today = timezone.localdate()
        dates = [
            today,
            today - timedelta(days=1),
            today - timedelta(days=5),
            today - timedelta(days=6),
            today - timedelta(days=7),
        ]
        current, longest = compute_streaks(dates)
        assert current == 2
        assert longest == 3

    def test_streak_counts_from_yesterday_too(self):
        # If user solved yesterday but not yet today, streak still counts as 1.
        today = timezone.localdate()
        dates = [today - timedelta(days=1)]
        current, _ = compute_streaks(dates)
        assert current == 1
