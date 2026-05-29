"""Auth + user endpoints."""

from __future__ import annotations

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import EmailVerificationToken, PasswordResetToken
from .serializers import (
    ChangePasswordSerializer,
    EmailVerifySerializer,
    GrindMateTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    UserSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    """POST /api/v1/auth/register/ - create a new user."""

    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "register"


class LoginView(TokenObtainPairView):
    """POST /api/v1/auth/login/ - return access + refresh tokens and user data."""

    serializer_class = GrindMateTokenObtainPairSerializer
    permission_classes = (permissions.AllowAny,)


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ - blacklist the refresh token."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *_args, **_kwargs):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(
                {"detail": "Refresh token required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh).blacklist()
        except Exception:
            return Response(
                {"detail": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/auth/me/ - current user's profile."""

    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """POST /api/v1/auth/change-password/."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *_args, **_kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class VerifyEmailView(APIView):
    """POST /api/v1/auth/verify-email/ - consume a signup token."""

    permission_classes = (permissions.AllowAny,)

    def post(self, request, *_args, **_kwargs):
        serializer = EmailVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = EmailVerificationToken.objects.select_related("user").get(
                token=serializer.validated_data["token"],
            )
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {"detail": "Invalid token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not token.is_usable():
            return Response(
                {"detail": "Token expired or already used."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token.consume()
        token.user.is_email_verified = True
        token.user.save(update_fields=["is_email_verified"])
        return Response({"detail": "Email verified."})


class ResendVerificationView(APIView):
    """POST /api/v1/auth/resend-verification/ - send a fresh verification link.

    Always returns 202 so attackers can't enumerate registered emails.
    """

    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "resend_verification"

    def post(self, request, *_args, **_kwargs):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email__iexact=email, is_email_verified=False).first()
        if user is not None:
            token = EmailVerificationToken.objects.create(user=user)
            verify_link = f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?token={token.token}"
            send_mail(
                subject="GrindMate - verify your email",
                message=(
                    f"Hi {user.name},\n\n"
                    f"Verify your email to start using GrindMate:\n{verify_link}\n\n"
                    "This link expires in 24 hours."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info("Resent verification token for user_id=%s", user.id)

        return Response(
            {"detail": "If that email belongs to an unverified account, a new link is on the way."},
            status=status.HTTP_202_ACCEPTED,
        )


class PasswordResetRequestView(APIView):
    """POST /api/v1/auth/password-reset/request/ - send a reset link.

    Always returns 202 to avoid leaking which emails are registered.
    """

    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "password_reset"

    def post(self, request, *_args, **_kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user is not None:
            token = PasswordResetToken.objects.create(user=user)
            reset_link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password/{token.token}"
            send_mail(
                subject="GrindMate - reset your password",
                message=(
                    f"Hi {user.name},\n\n"
                    f"Reset your GrindMate password:\n{reset_link}\n\n"
                    "This link expires in 1 hour. If you didn't request this, ignore the email."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info("Issued password reset token for user_id=%s", user.id)

        return Response(
            {"detail": "If that email exists, a reset link is on the way."},
            status=status.HTTP_202_ACCEPTED,
        )


class PasswordResetConfirmView(APIView):
    """POST /api/v1/auth/password-reset/confirm/ - consume a reset token."""

    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "password_reset"

    def post(self, request, *_args, **_kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = PasswordResetToken.objects.select_related("user").get(
                token=serializer.validated_data["token"],
            )
        except PasswordResetToken.DoesNotExist:
            return Response(
                {"detail": "Invalid or expired reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not token.is_usable():
            return Response(
                {"detail": "Invalid or expired reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token.consume()
        token.user.set_password(serializer.validated_data["new_password"])
        token.user.save(update_fields=["password"])
        return Response({"detail": "Password updated. You can log in now."})
