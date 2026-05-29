"""End-to-end test of verify_account / sync_account / backfill_problem_meta."""

from __future__ import annotations

import pytest
import responses
from django.conf import settings

from apps.leetcode.factories import LeetCodeAccountFactory
from apps.leetcode.models import Problem, SubmissionLog, SyncStatus
from apps.leetcode.sync import (
    backfill_problem_meta,
    sync_account,
    verify_account,
)
from apps.users.factories import UserFactory

pytestmark = pytest.mark.django_db
LC_URL = settings.LEETCODE_GRAPHQL_URL


def _profile_response(handle="anveet"):
    return {
        "data": {
            "matchedUser": {
                "username": handle,
                "profile": {"ranking": 9999},
                "submitStats": {
                    "acSubmissionNum": [
                        {"difficulty": "All", "count": 2},
                        {"difficulty": "Easy", "count": 1},
                        {"difficulty": "Medium", "count": 1},
                        {"difficulty": "Hard", "count": 0},
                    ],
                },
            },
        },
    }


def _recent_response():
    return {
        "data": {
            "recentAcSubmissionList": [
                {"id": "1", "title": "Two Sum", "titleSlug": "two-sum", "timestamp": "1714780800"},
                {
                    "id": "2",
                    "title": "Add Two Numbers",
                    "titleSlug": "add-two-numbers",
                    "timestamp": "1714694400",
                },
            ],
        },
    }


def _question_response(slug, difficulty="Easy"):
    return {
        "data": {
            "question": {
                "questionFrontendId": "1",
                "title": slug.replace("-", " ").title(),
                "titleSlug": slug,
                "difficulty": difficulty,
                "isPaidOnly": False,
                "topicTags": [{"name": "Array", "slug": "array"}],
            },
        },
    }


@responses.activate
def test_verify_account_only_fetches_profile():
    """verify_account is the fast path: a single LeetCode call, no submissions."""
    user = UserFactory()
    account = LeetCodeAccountFactory(user=user, handle="anveet", sync_status=SyncStatus.PENDING)
    responses.post(LC_URL, json=_profile_response("anveet"))

    result = verify_account(account)

    assert result.error is None
    assert result.new_solves == 0
    assert len(responses.calls) == 1  # only profile, no recent, no question
    account.refresh_from_db()
    assert account.sync_status == SyncStatus.OK
    assert account.total_solved == 2
    assert account.easy_solved == 1
    assert SubmissionLog.objects.count() == 0


@responses.activate
def test_sync_creates_placeholder_problems_and_submissions():
    """sync_account makes exactly 2 LeetCode calls (profile + recent); new slugs
    are stored as placeholders with empty difficulty for the backfill cron."""
    user = UserFactory()
    account = LeetCodeAccountFactory(user=user, handle="anveet", sync_status=SyncStatus.PENDING)
    responses.post(LC_URL, json=_profile_response("anveet"))
    responses.post(LC_URL, json=_recent_response())

    result = sync_account(account)

    assert result.error is None
    assert result.new_solves == 2
    assert result.problems_resolved == 2
    assert len(responses.calls) == 2  # no per-problem call

    account.refresh_from_db()
    assert account.sync_status == SyncStatus.OK
    assert Problem.objects.count() == 2
    # Placeholders have empty difficulty until backfill runs.
    assert set(Problem.objects.values_list("difficulty", flat=True)) == {""}
    assert SubmissionLog.objects.count() == 2


@responses.activate
def test_sync_is_idempotent_for_same_solves():
    user = UserFactory()
    account = LeetCodeAccountFactory(user=user, handle="anveet")

    responses.post(LC_URL, json=_profile_response("anveet"))
    responses.post(LC_URL, json=_recent_response())
    sync_account(account)

    responses.post(LC_URL, json=_profile_response("anveet"))
    responses.post(LC_URL, json=_recent_response())
    result = sync_account(account)

    assert result.new_solves == 0
    assert result.problems_resolved == 0
    assert SubmissionLog.objects.count() == 2


@responses.activate
def test_sync_records_failure_on_user_not_found():
    user = UserFactory()
    account = LeetCodeAccountFactory(user=user, handle="ghost", sync_status=SyncStatus.PENDING)
    responses.post(LC_URL, json={"data": {"matchedUser": None}})

    result = sync_account(account)

    assert result.error is not None
    account.refresh_from_db()
    assert account.sync_status == SyncStatus.FAILED
    assert "ghost" in account.last_sync_error


@responses.activate
def test_backfill_fills_placeholder_metadata():
    """backfill_problem_meta updates a placeholder Problem with real metadata."""
    placeholder = Problem.objects.create(
        title_slug="two-sum",
        title="Two Sum",
        difficulty="",
        topic_tags=[],
    )
    responses.post(LC_URL, json=_question_response("two-sum", "Easy"))

    backfill_problem_meta("two-sum")

    placeholder.refresh_from_db()
    assert placeholder.difficulty == "easy"
    assert placeholder.topic_tags == ["array"]
    assert placeholder.is_premium is False
