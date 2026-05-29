"""Cache-invalidation signals for the leetcode app.

When a new SubmissionLog lands (auto sync or manual mark), we drop the
leaderboard cache for every group the user belongs to so the next read
recomputes against the fresh data.
"""

from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.groups.leaderboard import invalidate_group_leaderboard

from .models import SubmissionLog

logger = logging.getLogger(__name__)


@receiver(post_save, sender=SubmissionLog)
def invalidate_leaderboards_on_solve(sender, instance: SubmissionLog, created: bool, **kwargs):
    if not created:
        return

    group_ids = list(
        instance.user.memberships.values_list("group__public_id", flat=True),
    )
    for public_id in group_ids:
        invalidate_group_leaderboard(str(public_id))

    if group_ids:
        logger.debug(
            "Invalidated leaderboard cache for %d group(s) after solve %s",
            len(group_ids),
            instance.pk,
        )
