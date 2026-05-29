"""factory_boy factories for the leetcode app."""

from __future__ import annotations

import factory
from django.utils import timezone

from apps.users.factories import UserFactory

from .models import Difficulty, LeetCodeAccount, Problem, SubmissionLog, SyncStatus


class LeetCodeAccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LeetCodeAccount
        django_get_or_create = ("handle",)

    user = factory.SubFactory(UserFactory)
    handle = factory.Sequence(lambda n: f"handle{n}")
    sync_status = SyncStatus.OK
    last_synced_at = factory.LazyFunction(timezone.now)


class ProblemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Problem
        django_get_or_create = ("title_slug",)

    title_slug = factory.Sequence(lambda n: f"two-sum-{n}")
    title = factory.LazyAttribute(lambda obj: obj.title_slug.replace("-", " ").title())
    difficulty = Difficulty.EASY
    topic_tags = factory.List(["array", "hash-table"])
    is_premium = False
    leetcode_id = factory.Sequence(lambda n: n + 1)


class SubmissionLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SubmissionLog

    user = factory.SubFactory(UserFactory)
    problem = factory.SubFactory(ProblemFactory)
    solved_at = factory.LazyFunction(timezone.now)
    source = SubmissionLog.SOURCE_AUTO
