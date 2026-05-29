"""Celery tasks for LeetCode sync.

Periodic schedule is configured in apps/leetcode/apps.py (Celery Beat).
"""

from __future__ import annotations

import logging

from celery import shared_task

from .models import LeetCodeAccount, SyncStatus
from .sync import sync_account

logger = logging.getLogger(__name__)


@shared_task(
    name="leetcode.sync_account",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=30,
    retry_jitter=True,
    max_retries=3,
)
def sync_account_task(self, account_id: int) -> dict:
    """Sync a single LeetCodeAccount by id."""
    try:
        account = LeetCodeAccount.objects.select_related("user").get(pk=account_id)
    except LeetCodeAccount.DoesNotExist:
        logger.info("LeetCodeAccount id=%s gone - skipping sync.", account_id)
        return {"skipped": True}

    result = sync_account(account)
    logger.info(
        "Sync complete for %s: new_solves=%s status=%s",
        account.handle,
        result.new_solves,
        account.sync_status,
    )
    return {
        "handle": account.handle,
        "new_solves": result.new_solves,
        "total_solved": result.total_solved,
        "problems_resolved": result.problems_resolved,
        "error": result.error,
    }


@shared_task(name="leetcode.sync_all_accounts")
def sync_all_accounts() -> dict:
    """Fan out per-account sync tasks. Called every N hours by Celery Beat."""
    pending = LeetCodeAccount.objects.exclude(sync_status=SyncStatus.UNVERIFIED)
    queued = 0
    for account_id in pending.values_list("id", flat=True):
        sync_account_task.delay(account_id)
        queued += 1
    logger.info("Queued LeetCode sync for %s account(s).", queued)
    return {"queued": queued}
