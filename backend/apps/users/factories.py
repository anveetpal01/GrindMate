"""factory_boy factories for users."""

from __future__ import annotations

import factory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@grindmate.test")
    username = factory.Sequence(lambda n: f"user{n}")
    display_name = factory.Faker("name")
    is_active = True
    is_email_verified = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        self.set_password(extracted or "testpass123!")
        self.save()


class StaffUserFactory(UserFactory):
    is_staff = True


class SuperUserFactory(UserFactory):
    is_staff = True
    is_superuser = True
    is_email_verified = True
