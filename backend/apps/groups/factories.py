"""factory_boy factories for the groups app."""

from __future__ import annotations

from datetime import timedelta

import factory
from django.utils import timezone

from apps.users.factories import UserFactory

from .models import Group, GroupInvite, GroupMembership


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Group

    name = factory.Sequence(lambda n: f"Group {n}")
    description = factory.Faker("sentence")
    owner = factory.SubFactory(UserFactory)

    @factory.post_generation
    def add_owner_membership(self, create, extracted, **kwargs):
        if not create:
            return
        GroupMembership.objects.get_or_create(
            group=self,
            user=self.owner,
            defaults={"role": GroupMembership.ROLE_ADMIN},
        )


class GroupMembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GroupMembership

    group = factory.SubFactory(GroupFactory)
    user = factory.SubFactory(UserFactory)
    role = GroupMembership.ROLE_MEMBER


class GroupInviteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GroupInvite

    group = factory.SubFactory(GroupFactory)
    created_by = factory.SelfAttribute("group.owner")
    expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
