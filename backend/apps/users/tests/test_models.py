"""Tests for User model and EmailVerificationToken behaviour."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time

from apps.users.factories import UserFactory
from apps.users.models import EmailVerificationToken, User

pytestmark = pytest.mark.django_db


class TestUserModel:
    def test_create_user_with_email_works(self):
        user = User.objects.create_user(
            email="anveet@grindmate.test",
            username="anveet",
            password="strongpass1!",
        )
        assert user.email == "anveet@grindmate.test"
        assert user.check_password("strongpass1!")
        assert not user.is_staff and not user.is_superuser

    def test_create_user_without_email_raises(self):
        with pytest.raises(ValueError, match="email"):
            User.objects.create_user(email="", username="x", password="p")

    def test_create_user_without_username_raises(self):
        with pytest.raises(ValueError, match="username"):
            User.objects.create_user(email="x@y.com", password="p")

    def test_create_superuser_sets_flags(self):
        admin = User.objects.create_superuser(
            email="admin@grindmate.test",
            username="admin",
            password="p1!",
        )
        assert admin.is_staff and admin.is_superuser and admin.is_email_verified

    def test_str_returns_username(self):
        user = UserFactory(username="anveet")
        assert str(user) == "anveet"


class TestEmailVerificationToken:
    def test_token_is_unique_per_call(self):
        user = UserFactory()
        t1 = EmailVerificationToken.objects.create(user=user)
        t2 = EmailVerificationToken.objects.create(user=user)
        assert t1.token != t2.token

    def test_fresh_token_is_usable(self):
        user = UserFactory()
        token = EmailVerificationToken.objects.create(user=user)
        assert token.is_usable()

    def test_consumed_token_is_unusable(self):
        user = UserFactory()
        token = EmailVerificationToken.objects.create(user=user)
        token.consume()
        assert not token.is_usable()
        assert token.used_at is not None

    def test_expired_token_is_unusable(self):
        user = UserFactory()
        with freeze_time(timezone.now() - timedelta(hours=25)):
            token = EmailVerificationToken.objects.create(user=user)
        assert token.is_expired()
        assert not token.is_usable()


class TestUserDeletionReassignsOwnedGroups:
    """The pre_delete signal must handle Group.owner PROTECT before user delete."""

    def test_ownership_transfers_to_other_admin(self):
        from apps.groups.factories import GroupFactory
        from apps.groups.models import Group, GroupMembership

        owner = UserFactory()
        other_admin = UserFactory()
        group = GroupFactory(owner=owner)  # adds owner as admin member
        GroupMembership.objects.create(
            group=group,
            user=other_admin,
            role=GroupMembership.ROLE_ADMIN,
        )

        owner.delete()

        group.refresh_from_db()
        assert group.owner == other_admin
        assert Group.objects.filter(pk=group.pk).exists()

    def test_member_gets_promoted_when_no_other_admin(self):
        from apps.groups.factories import GroupFactory
        from apps.groups.models import GroupMembership

        owner = UserFactory()
        member = UserFactory()
        group = GroupFactory(owner=owner)
        GroupMembership.objects.create(
            group=group,
            user=member,
            role=GroupMembership.ROLE_MEMBER,
        )

        owner.delete()

        group.refresh_from_db()
        assert group.owner == member
        assert group.memberships.get(user=member).role == GroupMembership.ROLE_ADMIN

    def test_orphan_group_is_deleted(self):
        from apps.groups.factories import GroupFactory
        from apps.groups.models import Group

        owner = UserFactory()
        group = GroupFactory(owner=owner)  # sole admin/member

        owner.delete()

        assert not Group.objects.filter(pk=group.pk).exists()
