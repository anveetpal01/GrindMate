"""Serializers for the groups app."""

from __future__ import annotations

from rest_framework import serializers

from apps.users.serializers import UserSerializer

from .models import Group, GroupInvite, GroupMembership


class GroupMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = GroupMembership
        fields = ("user", "role", "joined_at")


class GroupSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = (
            "public_id",
            "name",
            "description",
            "owner",
            "member_count",
            "role",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("public_id", "owner", "member_count", "created_at", "updated_at")

    def get_role(self, obj: Group) -> str | None:
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return None
        membership = next(
            (m for m in obj.memberships.all() if m.user_id == request.user.id),
            None,
        )
        return membership.role if membership else None


class GroupInviteSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = GroupInvite
        fields = (
            "token",
            "expires_at",
            "max_uses",
            "use_count",
            "revoked",
            "is_active",
            "created_at",
        )
        read_only_fields = (
            "token",
            "use_count",
            "is_active",
            "created_at",
        )


class LeaderboardRowSerializer(serializers.Serializer):
    """Read-only serializer that mirrors the LeaderboardRow dataclass."""

    rank = serializers.IntegerField()
    public_id = serializers.CharField()
    username = serializers.CharField()
    display_name = serializers.CharField()
    avatar_url = serializers.CharField()
    total_solved = serializers.IntegerField()
    easy_solved = serializers.IntegerField()
    medium_solved = serializers.IntegerField()
    hard_solved = serializers.IntegerField()
    score = serializers.IntegerField()
    current_streak = serializers.IntegerField()
    longest_streak = serializers.IntegerField()
