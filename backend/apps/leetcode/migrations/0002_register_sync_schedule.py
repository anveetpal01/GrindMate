"""Data migration - register the periodic LeetCode sync task with Celery Beat.

This is the "show-a-data-migration in PR" deliverable - django-celery-beat
stores schedules in the database, and we want every fresh deploy to come up
with the sync already wired without anyone clicking through admin.
"""
from __future__ import annotations

import json

from django.conf import settings
from django.db import migrations


def register_sync_schedule(apps, schema_editor):
    IntervalSchedule = apps.get_model("django_celery_beat", "IntervalSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=settings.LEETCODE_SYNC_INTERVAL_HOURS,
        period="hours",
    )

    PeriodicTask.objects.update_or_create(
        name="leetcode.sync_all_accounts",
        defaults={
            "task": "leetcode.sync_all_accounts",
            "interval": schedule,
            "enabled": True,
            "kwargs": json.dumps({}),
            "description": (
                "Fan-out per-account LeetCode sync - runs every "
                f"{settings.LEETCODE_SYNC_INTERVAL_HOURS}h."
            ),
        },
    )


def unregister_sync_schedule(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(name="leetcode.sync_all_accounts").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("leetcode", "0001_initial"),
        ("django_celery_beat", "0019_alter_periodictasks_options"),
    ]

    operations = [
        migrations.RunPython(register_sync_schedule, unregister_sync_schedule),
    ]
