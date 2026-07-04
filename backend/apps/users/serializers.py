"""Serializers for the users app."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import exceptions, serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Public-facing user representation."""

    class Meta:
        model = User
        fields = (
            "public_id",
            "username",
            "email",
            "display_name",
            "avatar_url",
            "timezone",
            "is_email_verified",
            "date_joined",
        )
        read_only_fields = ("public_id", "is_email_verified", "date_joined")


class RegisterSerializer(serializers.ModelSerializer):
    """Sign-up payload - creates the user; token issuance happens in the view."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("email", "username", "display_name", "password", "password_confirm")

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class GrindMateTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login serializer that also returns the user object so the frontend
    avoids a second `/me` round-trip on login."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_email_verified:
            raise exceptions.AuthenticationFailed(
                "Email not verified. Check your inbox for the verification link "
                "or request a new one.",
                code="email_not_verified",
            )
        data["user"] = UserSerializer(self.user).data
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value


class EmailVerifySerializer(serializers.Serializer):
    token = serializers.CharField(max_length=128)


class VerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.RegexField(r"^\d{6}$", error_messages={"invalid": "Enter the 6-digit code."})


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=128)
    new_password = serializers.CharField(required=True, validators=[validate_password])
