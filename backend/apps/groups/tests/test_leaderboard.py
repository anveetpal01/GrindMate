"""Tests for the leaderboard query."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APIClient

from apps.groups.factories import GroupFactory, GroupMembershipFactory
from apps.groups.leaderboard import compute_leaderboard
from apps.leetcode.factories import ProblemFactory, SubmissionLogFactory
from apps.users.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def freeze_to_wednesday():
    """Pin "now" to mid-week so weekly-window tests are deterministic."""
    with freeze_time("2026-05-06 12:00:00"):
        yield


def _solve(user, *, difficulty="easy", days_ago=0):
    return SubmissionLogFactory(
        user=user,
        problem=ProblemFactory(difficulty=difficulty),
        solved_at=timezone.now() - timedelta(days=days_ago),
    )


def test_leaderboard_orders_by_score_desc():
    group = GroupFactory()
    a, b, c = UserFactory(username="a"), UserFactory(username="b"), UserFactory(username="c")
    for u in (a, b, c):
        GroupMembershipFactory(group=group, user=u)

    # b: 2 hard solves = 10pts
    _solve(b, difficulty="hard")
    _solve(b, difficulty="hard")
    # a: 3 medium = 9pts
    _solve(a, difficulty="medium")
    _solve(a, difficulty="medium")
    _solve(a, difficulty="medium")
    # c: 1 easy = 1pt
    _solve(c, difficulty="easy")

    rows = compute_leaderboard(group, "all-time")
    usernames = [r.username for r in rows[:3]]
    assert usernames[0] == "b"  # highest score
    assert usernames[1] == "a"
    assert usernames[2] == "c"


def test_leaderboard_period_weekly_excludes_old_solves():
    group = GroupFactory()
    user = UserFactory()
    GroupMembershipFactory(group=group, user=user)

    _solve(user, difficulty="hard", days_ago=2)  # this week
    _solve(user, difficulty="hard", days_ago=20)  # last month

    rows = compute_leaderboard(group, "weekly")
    me = next(r for r in rows if r.username == user.username)
    assert me.total_solved == 1
    assert me.score == 5  # one hard


def test_leaderboard_includes_streaks():
    group = GroupFactory()
    user = UserFactory()
    GroupMembershipFactory(group=group, user=user)

    for d in range(3):  # solves on today, yesterday, 2 days ago
        _solve(user, days_ago=d)

    rows = compute_leaderboard(group, "all-time")
    me = next(r for r in rows if r.username == user.username)
    assert me.current_streak == 3


def test_leaderboard_includes_owner_with_zero_solves():
    """Members without solves still show up at the bottom."""
    group = GroupFactory()
    rows = compute_leaderboard(group, "all-time")
    assert len(rows) == 1
    assert rows[0].total_solved == 0


class TestLeaderboardEndpoint:
    def test_member_sees_leaderboard(self):
        client = APIClient()
        me = UserFactory()
        group = GroupFactory()
        GroupMembershipFactory(group=group, user=me)
        client.force_authenticate(user=me)

        url = reverse("v1:groups:leaderboard", args=[group.public_id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["period"] == "weekly"
        assert isinstance(body["rows"], list)

    def test_invalid_period_400(self):
        client = APIClient()
        me = UserFactory()
        group = GroupFactory()
        GroupMembershipFactory(group=group, user=me)
        client.force_authenticate(user=me)

        url = reverse("v1:groups:leaderboard", args=[group.public_id])
        response = client.get(url + "?period=eternal")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_non_member_forbidden(self):
        client = APIClient()
        me = UserFactory()
        group = GroupFactory()  # me is NOT in this group
        client.force_authenticate(user=me)

        url = reverse("v1:groups:leaderboard", args=[group.public_id])
        response = client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
