"""Safely delete a user and everything that hangs off them.

Handles the Group.owner PROTECT constraint: an owned group is reassigned to
another member (admin preferred, then earliest to join); if the group has no
other members it is deleted. Everything else (leetcode account, submissions,
memberships, tokens) cascades via the ORM.

Examples:
    python manage.py delete_user anveetpal12@gmail.com          # by email
    python manage.py delete_user someusername                   # by username
    python manage.py delete_user --id 1                         # by primary key
    python manage.py delete_user anveetpal12@gmail.com --dry-run  # preview only
    python manage.py delete_user anveetpal12@gmail.com --yes      # skip prompt
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.groups.models import Group, GroupMembership

User = get_user_model()


class Command(BaseCommand):
    help = "Delete a user (by email, username, or --id) and all related data."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "identifier",
            nargs="?",
            help="Email or username of the user to delete.",
        )
        parser.add_argument("--id", type=int, help="Delete by primary key instead.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without touching the database.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip the confirmation prompt.",
        )

    def handle(self, *args, **options) -> None:
        user = self._resolve_user(options)

        owned = list(Group.objects.filter(owner=user))
        related = {
            "leetcode account": getattr(user, "leetcode_account", None) is not None,
            "submissions": user.submissions.count(),
            "group memberships": user.memberships.count(),
            "owned groups": len(owned),
        }

        self.stdout.write(
            f"User: {user.username} <{user.email}> (id={user.pk})"
        )
        for label, value in related.items():
            self.stdout.write(f"  - {label}: {value}")

        for group in owned:
            successor = self._pick_successor(group, user)
            action = (
                f"reassign to {successor.username}"
                if successor
                else "DELETE (no other members)"
            )
            self.stdout.write(f"  owned group '{group.name}': {action}")

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run — nothing deleted."))
            return

        if not options["yes"]:
            confirm = input(f"Delete {user.email}? Type 'yes' to confirm: ")
            if confirm.strip().lower() != "yes":
                self.stdout.write("Aborted.")
                return

        with transaction.atomic():
            for group in owned:
                successor = self._pick_successor(group, user)
                if successor:
                    group.owner = successor
                    group.save(update_fields=["owner"])
                else:
                    group.delete()
            user.delete()

        self.stdout.write(self.style.SUCCESS(f"Deleted {user.email}."))

    def _resolve_user(self, options):
        if options.get("id") is not None:
            try:
                return User.objects.get(pk=options["id"])
            except User.DoesNotExist:
                raise CommandError(f"No user with id={options['id']}.") from None

        identifier = options.get("identifier")
        if not identifier:
            raise CommandError("Provide an email/username, or use --id.")

        lookup = "email" if "@" in identifier else "username"
        try:
            return User.objects.get(**{lookup: identifier})
        except User.DoesNotExist:
            raise CommandError(f"No user with {lookup}={identifier!r}.") from None

    @staticmethod
    def _pick_successor(group: Group, leaving) -> object | None:
        """Prefer another admin, then the earliest joiner; None if nobody left."""
        others = group.memberships.exclude(user=leaving)
        successor = (
            others.filter(role=GroupMembership.ROLE_ADMIN).order_by("joined_at").first()
            or others.order_by("joined_at").first()
        )
        return successor.user if successor else None
