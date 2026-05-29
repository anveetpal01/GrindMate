"""Tests for the LeetCode service layer (HTTP mocked with `responses`)."""

from __future__ import annotations

import pytest
import responses
from django.conf import settings

from apps.leetcode.services import (
    LeetCodeAPIError,
    LeetCodeRateLimited,
    LeetCodeUserNotFound,
    fetch_problem_meta,
    fetch_profile_summary,
    fetch_recent_solves,
)

LC_URL = settings.LEETCODE_GRAPHQL_URL


def _profile_payload(handle: str = "anveet"):
    return {
        "data": {
            "matchedUser": {
                "username": handle,
                "profile": {"ranking": 12345},
                "submitStats": {
                    "acSubmissionNum": [
                        {"difficulty": "All", "count": 87},
                        {"difficulty": "Easy", "count": 42},
                        {"difficulty": "Medium", "count": 35},
                        {"difficulty": "Hard", "count": 10},
                    ],
                },
            },
        },
    }


def _recent_payload():
    return {
        "data": {
            "recentAcSubmissionList": [
                {"id": "1", "title": "Two Sum", "titleSlug": "two-sum", "timestamp": "1714780800"},
                {"id": "2", "title": "3Sum", "titleSlug": "3sum", "timestamp": "1714694400"},
            ],
        },
    }


def _question_payload():
    return {
        "data": {
            "question": {
                "questionFrontendId": "1",
                "title": "Two Sum",
                "titleSlug": "two-sum",
                "difficulty": "Easy",
                "isPaidOnly": False,
                "topicTags": [{"name": "Array", "slug": "array"}],
            },
        },
    }


@responses.activate
def test_fetch_profile_summary_parses_counts():
    responses.post(LC_URL, json=_profile_payload())

    summary = fetch_profile_summary("anveet")

    assert summary.handle == "anveet"
    assert summary.ranking == 12345
    assert summary.total_solved == 87
    assert summary.easy_solved == 42
    assert summary.medium_solved == 35
    assert summary.hard_solved == 10


@responses.activate
def test_fetch_profile_summary_unknown_user():
    responses.post(LC_URL, json={"data": {"matchedUser": None}})

    with pytest.raises(LeetCodeUserNotFound):
        fetch_profile_summary("ghost")


@responses.activate
def test_fetch_profile_summary_graphql_errors():
    responses.post(LC_URL, json={"errors": [{"message": "boom"}], "data": None})

    with pytest.raises(LeetCodeAPIError):
        fetch_profile_summary("anveet")


@responses.activate
def test_fetch_recent_solves_parses_timestamps():
    responses.post(LC_URL, json=_recent_payload())

    solves = fetch_recent_solves("anveet", limit=10)

    assert len(solves) == 2
    assert solves[0].title_slug == "two-sum"
    assert solves[0].solved_at.tzinfo is not None  # tz-aware


@responses.activate
def test_fetch_problem_meta_parses_difficulty_and_tags():
    responses.post(LC_URL, json=_question_payload())

    meta = fetch_problem_meta("two-sum")

    assert meta.title_slug == "two-sum"
    assert meta.difficulty == "easy"
    assert meta.topic_tags == ["array"]
    assert meta.leetcode_id == 1


@responses.activate
def test_rate_limit_retries_then_raises():
    # 3 attempts × 429 → final raise
    for _ in range(3):
        responses.post(LC_URL, status=429, body="rate limit")

    with pytest.raises(LeetCodeRateLimited):
        fetch_profile_summary("anveet")


@responses.activate
def test_rate_limit_then_recovers():
    responses.post(LC_URL, status=429, body="slow down")
    responses.post(LC_URL, json=_profile_payload())

    summary = fetch_profile_summary("anveet")
    assert summary.handle == "anveet"
