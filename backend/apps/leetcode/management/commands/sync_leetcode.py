"""Manual LeetCode sync command.

python manage.py sync_leetcode --user=anveet
python manage.py sync_leetcode --all
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from apps.leetcode.models import LeetCodeAccount, SyncStatus
from apps.leetcode.sync import sync_account


class Command(BaseCommand):
    help = "Manually sync one or all linked LeetCode accounts."

    def add_arguments(self, parser) -> None:
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--user", help="Sync the LeetCode account for this username.")
        group.add_argument("--handle", help="Sync the LeetCode account with this handle.")
        group.add_argument("--all", action="store_true", help="Sync every linked account.")

    def handle(self, *args, **options) -> None:
        if options["all"]:
            qs = LeetCodeAccount.objects.exclude(sync_status=SyncStatus.UNVERIFIED)
            self.stdout.write(f"Syncing {qs.count()} account(s)…")
            for account in qs:
                self._sync_one(account)
            return

        if options.get("user"):
            try:
                account = LeetCodeAccount.objects.select_related("user").get(
                    user__username=options["user"],
                )
            except LeetCodeAccount.DoesNotExist as exc:
                raise CommandError(
                    f"No LeetCode account linked for user {options['user']!r}.",
                ) from exc
        else:
            try:
                account = LeetCodeAccount.objects.select_related("user").get(
                    handle__iexact=options["handle"],
                )
            except LeetCodeAccount.DoesNotExist as exc:
                raise CommandError(
                    f"No account with handle {options['handle']!r}.",
                ) from exc

        self._sync_one(account)

    def _sync_one(self, account: LeetCodeAccount) -> None:
        self.stdout.write(f"  → {account.user.username} ({account.handle})…")
        result = sync_account(account)
        if result.error:
            self.stderr.write(self.style.ERROR(f"    ✗ {result.error}"))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"    ✓ {result.new_solves} new (total {result.total_solved})",
                ),
            )
