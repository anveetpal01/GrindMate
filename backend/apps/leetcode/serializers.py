"""Serializers for the leetcode app."""

from __future__ import annotations

from rest_framework import serializers

from .models import LeetCodeAccount, Problem, SubmissionLog


class LeetCodeAccountSerializer(serializers.ModelSerializer):
    is_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = LeetCodeAccount
        fields = (
            "handle",
            "sync_status",
            "is_verified",
            "last_synced_at",
            "last_sync_error",
            "total_solved",
            "easy_solved",
            "medium_solved",
            "hard_solved",
            "ranking",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "sync_status",
            "is_verified",
            "last_synced_at",
            "last_sync_error",
            "total_solved",
            "easy_solved",
            "medium_solved",
            "hard_solved",
            "ranking",
            "created_at",
            "updated_at",
        )

    def validate_handle(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Handle required.")
        if not value.replace("-", "").replace("_", "").isalnum():
            raise serializers.ValidationError(
                "Handle should only contain letters, digits, dashes, and underscores.",
            )
        return value


class ProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = (
            "title_slug",
            "title",
            "difficulty",
            "topic_tags",
            "is_premium",
            "leetcode_id",
        )


class SubmissionLogSerializer(serializers.ModelSerializer):
    problem = ProblemSerializer(read_only=True)

    class Meta:
        model = SubmissionLog
        fields = ("id", "problem", "solved_at", "source", "created_at")


class ManualSubmissionSerializer(serializers.Serializer):
    """Manual mark-as-solved payload - used when auto-sync fails."""

    title_slug = serializers.SlugField(max_length=128)
    solved_at = serializers.DateTimeField(required=False)
