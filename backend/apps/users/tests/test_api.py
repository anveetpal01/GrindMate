"""Integration tests for users API endpoints."""

from __future__ import annotations

import pytest
from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.factories import UserFactory
from apps.users.models import EmailVerificationToken, PasswordResetToken

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def user():
    return UserFactory(username="anveet", email="anveet@grindmate.test")


@pytest.fixture
def authed_client(client, user) -> APIClient:
    client.force_authenticate(user=user)
    return client


class TestRegister:
    url = reverse("v1:users:register")

    def test_register_creates_user_and_token(self, client):
        payload = {
            "email": "new@grindmate.test",
            "username": "newbie",
            "display_name": "Newbie",
            "password": "strongpass1!",
            "password_confirm": "strongpass1!",
        }
        response = client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        # Email verification token should be issued by signal.
        assert EmailVerificationToken.objects.filter(user__email="new@grindmate.test").exists()

    def test_register_password_mismatch_fails(self, client):
        response = client.post(
            self.url,
            {
                "email": "x@grindmate.test",
                "username": "x",
                "password": "strongpass1!",
                "password_confirm": "different!1",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_email_fails(self, client, user):
        response = client.post(
            self.url,
            {
                "email": user.email,
                "username": "different",
                "password": "strongpass1!",
                "password_confirm": "strongpass1!",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestLogin:
    url = reverse("v1:users:login")

    def test_login_returns_tokens_and_user(self, client, user):
        response = client.post(
            self.url,
            {"email": user.email, "password": "testpass123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert "access" in body
        assert "refresh" in body
        assert body["user"]["username"] == user.username

    def test_login_wrong_password_fails(self, client, user):
        response = client.post(
            self.url,
            {"email": user.email, "password": "wrong"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_unverified_user_fails(self, client):
        unverified = UserFactory(is_email_verified=False)
        response = client.post(
            self.url,
            {"email": unverified.email, "password": "testpass123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "verif" in response.json().get("detail", "").lower()


class TestMe:
    url = reverse("v1:users:me")

    def test_me_requires_auth(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_returns_user(self, authed_client, user):
        response = authed_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == user.username

    def test_me_can_patch_display_name(self, authed_client):
        response = authed_client.patch(self.url, {"display_name": "Anveet K"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["display_name"] == "Anveet K"


class TestVerifyEmail:
    url = reverse("v1:users:verify_email")

    def test_valid_token_verifies_user(self, client):
        unverified = UserFactory(is_email_verified=False)
        token = EmailVerificationToken.objects.create(user=unverified)

        response = client.post(self.url, {"token": token.token}, format="json")
        assert response.status_code == status.HTTP_200_OK

        unverified.refresh_from_db()
        token.refresh_from_db()
        assert unverified.is_email_verified
        assert token.used_at is not None

    def test_invalid_token_rejected(self, client):
        response = client.post(self.url, {"token": "nonsense"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_used_token_rejected(self, client):
        unverified = UserFactory(is_email_verified=False)
        token = EmailVerificationToken.objects.create(user=unverified)
        token.consume()

        response = client.post(self.url, {"token": token.token}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestVerifyOtp:
    url = reverse("v1:users:verify_otp")

    def test_valid_otp_verifies_and_logs_in(self, client):
        unverified = UserFactory(is_email_verified=False)
        token = EmailVerificationToken.objects.create(user=unverified)

        response = client.post(
            self.url, {"email": unverified.email, "otp": token.otp}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert "access" in body
        assert "refresh" in body
        assert body["user"]["username"] == unverified.username

        unverified.refresh_from_db()
        token.refresh_from_db()
        assert unverified.is_email_verified
        assert token.used_at is not None

    def test_wrong_otp_rejected_and_counted(self, client):
        unverified = UserFactory(is_email_verified=False)
        token = EmailVerificationToken.objects.create(user=unverified, otp="111111")

        response = client.post(
            self.url, {"email": unverified.email, "otp": "222222"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        token.refresh_from_db()
        assert token.attempts == 1
        unverified.refresh_from_db()
        assert not unverified.is_email_verified

    def test_otp_locked_after_max_attempts(self, client):
        unverified = UserFactory(is_email_verified=False)
        token = EmailVerificationToken.objects.create(user=unverified, otp="111111")

        for _ in range(EmailVerificationToken.MAX_ATTEMPTS):
            client.post(self.url, {"email": unverified.email, "otp": "222222"}, format="json")

        # Correct code no longer works - token burned by brute-force guard.
        response = client.post(
            self.url, {"email": unverified.email, "otp": "111111"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        token.refresh_from_db()
        assert not token.is_usable()

    def test_latest_token_wins_after_resend(self, client):
        unverified = UserFactory(is_email_verified=False)
        old = EmailVerificationToken.objects.create(user=unverified, otp="111111")
        EmailVerificationToken.objects.create(user=unverified, otp="333333")

        # Old code is dead once a new one is issued.
        response = client.post(
            self.url, {"email": unverified.email, "otp": old.otp}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response = client.post(
            self.url, {"email": unverified.email, "otp": "333333"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_already_verified_rejected(self, client, user):
        response = client.post(
            self.url, {"email": user.email, "otp": "123456"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already verified" in response.json()["detail"].lower()

    def test_unknown_email_rejected_generically(self, client):
        response = client.post(
            self.url, {"email": "ghost@grindmate.test", "otp": "123456"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Invalid code."

    def test_malformed_otp_rejected(self, client):
        unverified = UserFactory(is_email_verified=False)
        response = client.post(
            self.url, {"email": unverified.email, "otp": "12ab56"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestResendVerification:
    url = reverse("v1:users:resend_verification")

    def test_resend_for_unverified_user_creates_token(self, client):
        unverified = UserFactory(is_email_verified=False)
        before = EmailVerificationToken.objects.filter(user=unverified).count()
        mail.outbox.clear()

        response = client.post(self.url, {"email": unverified.email}, format="json")

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert EmailVerificationToken.objects.filter(user=unverified).count() == before + 1
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [unverified.email]

    def test_resend_for_verified_user_is_silent(self, client, user):
        """Already-verified users get the same 202 (no enumeration)."""
        before = EmailVerificationToken.objects.filter(user=user).count()
        mail.outbox.clear()

        response = client.post(self.url, {"email": user.email}, format="json")

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert EmailVerificationToken.objects.filter(user=user).count() == before
        assert mail.outbox == []

    def test_resend_for_unknown_email_is_silent(self, client):
        mail.outbox.clear()
        response = client.post(self.url, {"email": "ghost@nope.test"}, format="json")
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert mail.outbox == []


class TestPasswordReset:
    request_url = reverse("v1:users:password_reset_request")
    confirm_url = reverse("v1:users:password_reset_confirm")

    def test_request_creates_token_and_sends_email(self, client, user):
        mail.outbox.clear()
        response = client.post(self.request_url, {"email": user.email}, format="json")

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert PasswordResetToken.objects.filter(user=user).count() == 1
        assert len(mail.outbox) == 1

    def test_request_for_unknown_email_is_silent(self, client):
        mail.outbox.clear()
        response = client.post(self.request_url, {"email": "ghost@nope.test"}, format="json")
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert PasswordResetToken.objects.count() == 0
        assert mail.outbox == []

    def test_confirm_updates_password(self, client, user):
        token = PasswordResetToken.objects.create(user=user)
        response = client.post(
            self.confirm_url,
            {"token": token.token, "new_password": "freshpass123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password("freshpass123!")
        token.refresh_from_db()
        assert token.used_at is not None

    def test_confirm_with_used_token_rejected(self, client, user):
        token = PasswordResetToken.objects.create(user=user)
        token.consume()
        response = client.post(
            self.confirm_url,
            {"token": token.token, "new_password": "freshpass123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_confirm_with_invalid_token_rejected(self, client):
        response = client.post(
            self.confirm_url,
            {"token": "nope", "new_password": "freshpass123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_confirm_validates_password_strength(self, client, user):
        token = PasswordResetToken.objects.create(user=user)
        response = client.post(
            self.confirm_url,
            {"token": token.token, "new_password": "short"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestChangePassword:
    url = reverse("v1:users:change_password")

    def test_correct_old_password_changes(self, authed_client, user):
        response = authed_client.post(
            self.url,
            {"old_password": "testpass123!", "new_password": "newstrongpass2@"},
            format="json",
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        user.refresh_from_db()
        assert user.check_password("newstrongpass2@")

    def test_wrong_old_password_fails(self, authed_client):
        response = authed_client.post(
            self.url,
            {"old_password": "wrong", "new_password": "newstrongpass2@"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
