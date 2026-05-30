"""User-related signals.

On signup: issues an email verification token and dispatches the email.
Owned-group reassignment on deletion lives on User.delete() (signals.py can't
catch it because PROTECT checks happen before pre_delete fires).
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import EmailVerificationToken, User

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def issue_email_verification(sender, instance: User, created: bool, **kwargs) -> None:
    if not created or instance.is_email_verified:
        return

    token = EmailVerificationToken.objects.create(user=instance)
    verify_link = f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?token={token.token}"

    logger.info("Issued email verification token for user_id=%s", instance.id)

    try:
        send_mail(
            subject="Welcome to GrindMate - verify your email",
            message=(
                f"Hi {instance.name},\n\n"
                f"Click the link below to verify your email and start grinding:\n"
                f"{verify_link}\n\n"
                "This link expires in 24 hours."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.email],
            fail_silently=False,
        )
    except Exception as exc:
        # Don't block signup if SMTP is down/misconfigured. User can request
        # a fresh link via /auth/resend-verification/ once email works.
        logger.error("Failed to send verification email to %s: %s", instance.email, exc)
