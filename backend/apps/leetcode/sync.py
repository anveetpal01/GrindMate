"""Sync orchestration - wraps the LeetCode service calls, persists the result.

Public entry points:
    verify_account(account)         - fast: pull profile only, refresh aggregates
    sync_account(account)           - pull profile + recent solves; writes Problem
                                      placeholders (lazy metadata via backfill)
    upsert_problem(slug, *, client) - resolve a problem slug to a Problem row
                                      (defer_meta=True skips the LeetCode call)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from .models import LeetCodeAccount, Problem, SubmissionLog, SyncStatus
from .services import (
    LeetCodeAPIError,
    LeetCodeClient,
    fetch_problem_meta,
    fetch_profile_summary,
    fetch_recent_solves,
)

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    new_solves: int
    total_solved: int
    problems_resolved: int
    error: str | None = None


def upsert_problem(
    slug: str,
    *,
    client: LeetCodeClient | None = None,
    defer_meta: bool = False,
    fallback_title: str | None = None,
) -> Problem:
    """Get-or-create a Problem row for `slug`.

    With defer_meta=True, creates a placeholder row (difficulty="") without
    hitting the LeetCode API - used during account sync to keep per-request
    latency bounded. The placeholder is later filled in by
    `manage.py backfill_problems` (or its cron endpoint).
    """
    problem = Problem.objects.filter(title_slug=slug).first()
    if problem:
        return problem

    if defer_meta:
        return Problem.objects.create(
            title_slug=slug,
            title=fallback_title or slug.replace("-", " ").title(),
            difficulty="",
            topic_tags=[],
            is_premium=False,
        )

    meta = fetch_problem_meta(slug, client=client)
    problem, _created = Problem.objects.update_or_create(
        title_slug=meta.title_slug,
        defaults={
            "title": meta.title,
            "difficulty": meta.difficulty or "easy",
            "topic_tags": meta.topic_tags,
            "is_premium": meta.is_premium,
            "leetcode_id": meta.leetcode_id,
        },
    )
    return problem


def backfill_problem_meta(
    slug: str,
    *,
    client: LeetCodeClient | None = None,
) -> Problem:
    """Update an existing (placeholder) Problem row with full metadata.

    Used by `manage.py backfill_problems` and the cron endpoint to walk
    Problem rows that were created with difficulty="" during deferred sync.
    Raises LeetCodeAPIError on network failure - caller decides whether
    to skip or abort.
    """
    meta = fetch_problem_meta(slug, client=client)
    problem, _ = Problem.objects.update_or_create(
        title_slug=slug,
        defaults={
            "title": meta.title,
            "difficulty": meta.difficulty or "easy",
            "topic_tags": meta.topic_tags,
            "is_premium": meta.is_premium,
            "leetcode_id": meta.leetcode_id,
        },
    )
    return problem


def _apply_summary(account: LeetCodeAccount, summary) -> None:
    account.handle = summary.handle
    account.ranking = summary.ranking
    account.total_solved = summary.total_solved
    account.easy_solved = summary.easy_solved
    account.medium_solved = summary.medium_solved
    account.hard_solved = summary.hard_solved
    account.sync_status = SyncStatus.OK
    account.last_sync_error = ""
    account.last_synced_at = timezone.now()


def _record_failure(account: LeetCodeAccount, exc: Exception) -> SyncResult:
    logger.warning("LeetCode call failed for %s: %s", account.handle, exc)
    account.sync_status = SyncStatus.FAILED
    account.last_sync_error = str(exc)[:1000]
    account.last_synced_at = timezone.now()
    account.save(update_fields=["sync_status", "last_sync_error", "last_synced_at"])
    return SyncResult(
        new_solves=0,
        total_solved=account.total_solved,
        problems_resolved=0,
        error=str(exc),
    )


def verify_account(
    account: LeetCodeAccount,
    *,
    client: LeetCodeClient | None = None,
) -> SyncResult:
    """Fast path: single profile fetch to verify the handle and refresh stats.

    Used by the link-handle endpoint - no per-problem network calls, so it
    completes in ~2s and fits inside any reasonable HTTP timeout. Recent solves
    are picked up by the scheduled `sync_account` later (cron every 6h, or the
    user clicking 'Sync now').
    """
    client = client or LeetCodeClient()
    try:
        summary = fetch_profile_summary(account.handle, client=client)
    except LeetCodeAPIError as exc:
        return _record_failure(account, exc)

    _apply_summary(account, summary)
    account.save()
    return SyncResult(
        new_solves=0,
        total_solved=summary.total_solved,
        problems_resolved=0,
    )


def sync_account(
    account: LeetCodeAccount,
    *,
    client: LeetCodeClient | None = None,
) -> SyncResult:
    """Pull profile + recent solves for `account`, persist diff, update aggregates.

    Problem rows are created with a placeholder difficulty when first seen;
    `manage.py backfill_problems` fills the metadata asynchronously. This keeps
    sync latency at 2 LeetCode calls regardless of recent-solve count.
    """
    client = client or LeetCodeClient()

    try:
        summary = fetch_profile_summary(account.handle, client=client)
        recent = fetch_recent_solves(account.handle, client=client)
    except LeetCodeAPIError as exc:
        return _record_failure(account, exc)

    new_solves = 0
    problems_resolved = 0

    with transaction.atomic():
        for solve in recent:
            problem = Problem.objects.filter(title_slug=solve.title_slug).first()
            if problem is None:
                problem = upsert_problem(
                    solve.title_slug,
                    defer_meta=True,
                    fallback_title=solve.title,
                )
                problems_resolved += 1

            _log, created = SubmissionLog.objects.get_or_create(
                user=account.user,
                problem=problem,
                solved_at=solve.solved_at,
                defaults={"source": SubmissionLog.SOURCE_AUTO},
            )
            if created:
                new_solves += 1

        _apply_summary(account, summary)
        account.save()

    return SyncResult(
        new_solves=new_solves,
        total_solved=summary.total_solved,
        problems_resolved=problems_resolved,
    )
