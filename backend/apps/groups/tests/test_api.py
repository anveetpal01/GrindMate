"""Integration tests for groups API endpoints."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.groups.factories import GroupFactory, GroupInviteFactory, GroupMembershipFactory
from apps.groups.models import Group
from apps.users.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def me():
    return UserFactory(username="anveet")


@pytest.fixture
def authed_client(client, me):
    client.force_authenticate(user=me)
    return client


class TestCreateGroup:
    url = reverse("v1:groups:list_create")

    def test_create_makes_owner_admin(self, authed_client, me):
        response = authed_client.post(self.url, {"name": "NeetCode 150 Crew"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        group = Group.objects.get(name="NeetCode 150 Crew")
        assert group.owner == me
        assert group.memberships.filter(user=me, role="admin").exists()

    def test_list_returns_only_my_groups(self, authed_client, me):
        mine = GroupFactory(owner=me)
        not_mine = GroupFactory()

        response = authed_client.get(self.url)
        ids = {g["public_id"] for g in response.json()["results"]}
        assert str(mine.public_id) in ids
        assert str(not_mine.public_id) not in ids


class TestGroupDetail:
    def test_member_can_view(self, authed_client, me):
        group = GroupFactory()
        GroupMembershipFactory(group=group, user=me)

        url = reverse("v1:groups:detail", args=[group.public_id])
        response = authed_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_non_member_forbidden(self, authed_client):
        group = GroupFactory()
        url = reverse("v1:groups:detail", args=[group.public_id])
        response = authed_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_only_admin_can_patch(self, authed_client, me):
        group = GroupFactory()  # owner is some other user
        GroupMembershipFactory(group=group, user=me, role="member")

        url = reverse("v1:groups:detail", args=[group.public_id])
        response = authed_client.patch(url, {"name": "Sneaky rename"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestInviteFlow:
    def test_admin_creates_invite(self, authed_client, me):
        group = GroupFactory(owner=me)
        url = reverse("v1:groups:invite", args=[group.public_id])
        response = authed_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["is_active"]

    def test_member_cannot_create_invite(self, authed_client, me):
        group = GroupFactory()
        GroupMembershipFactory(group=group, user=me, role="member")
        url = reverse("v1:groups:invite", args=[group.public_id])
        response = authed_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_join_with_valid_invite(self, authed_client, me):
        invite = GroupInviteFactory()
        url = reverse("v1:groups:join", args=[invite.token])
        response = authed_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        assert invite.group.has_member(me)

    def test_join_idempotent_if_already_member(self, authed_client, me):
        invite = GroupInviteFactory()
        GroupMembershipFactory(group=invite.group, user=me)
        url = reverse("v1:groups:join", args=[invite.token])
        response = authed_client.post(url)
        assert response.status_code == status.HTTP_200_OK

    def test_revoked_invite_410(self, authed_client):
        invite = GroupInviteFactory(revoked=True)
        url = reverse("v1:groups:join", args=[invite.token])
        response = authed_client.post(url)
        assert response.status_code == status.HTTP_410_GONE

    def test_max_uses_enforced(self, authed_client, me):
        invite = GroupInviteFactory(max_uses=1, use_count=1)
        url = reverse("v1:groups:join", args=[invite.token])
        response = authed_client.post(url)
        assert response.status_code == status.HTTP_410_GONE


class TestLeaveGroup:
    def test_member_can_leave(self, authed_client, me):
        group = GroupFactory()
        GroupMembershipFactory(group=group, user=me)

        url = reverse("v1:groups:leave", args=[group.public_id])
        response = authed_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not group.has_member(me)

    def test_owner_cannot_leave(self, authed_client, me):
        group = GroupFactory(owner=me)
        url = reverse("v1:groups:leave", args=[group.public_id])
        response = authed_client.delete(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
