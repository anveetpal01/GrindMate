"""Backfill Problem metadata for rows created with a placeholder difficulty.

Examples:
    python manage.py backfill_problems              # 50 rows, default
    python manage.py backfill_problems --limit 100
    python manage.py backfill_problems --slug two-sum
"""

from __future__ import annotations

import time

from django.core.management.base import BaseCommand

from apps.leetcode.models import Problem
from apps.leetcode.services import LeetCodeAPIError, LeetCodeClient
from apps.leetcode.sync import backfill_problem_meta


class Command(BaseCommand):
    help = "Fill in metadata for Problem rows that have an empty difficulty."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of slugs to process this run.",
        )
        parser.add_argument(
            "--slug",
            help="Backfill a single slug regardless of current state.",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=1.0,
            help="Seconds to wait between requests (LeetCode rate-limit margin).",
        )

    def handle(self, *args, **options) -> None:
        if options.get("slug"):
            slugs = [options["slug"]]
        else:
            slugs = list(
                Problem.objects.filter(difficulty="").values_list("title_slug", flat=True)[
                    : options["limit"]
                ]
            )

        if not slugs:
            self.stdout.write("Nothing to backfill.")
            return

        self.stdout.write(f"Backfilling {len(slugs)} problem(s)...")
        client = LeetCodeClient()
        ok = fail = 0
        for slug in slugs:
            try:
                backfill_problem_meta(slug, client=client)
                self.stdout.write(self.style.SUCCESS(f"  + {slug}"))
                ok += 1
            except LeetCodeAPIError as exc:
                self.stderr.write(self.style.ERROR(f"  x {slug}: {exc}"))
                fail += 1
            time.sleep(options["sleep"])
        self.stdout.write(self.style.SUCCESS(f"Done. {ok} ok, {fail} failed."))
