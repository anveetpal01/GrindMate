"""Django admin for the leetcode app."""

from __future__ import annotations

from django.contrib import admin

from .models import LeetCodeAccount, Problem, SubmissionLog


@admin.register(LeetCodeAccount)
class LeetCodeAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "handle", "sync_status", "total_solved", "last_synced_at")
    list_filter = ("sync_status",)
    search_fields = ("user__username", "user__email", "handle")
    readonly_fields = (
        "total_solved",
        "easy_solved",
        "medium_solved",
        "hard_solved",
        "ranking",
        "last_synced_at",
        "last_sync_error",
        "created_at",
        "updated_at",
    )


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ("title", "title_slug", "difficulty", "leetcode_id", "is_premium")
    list_filter = ("difficulty", "is_premium")
    search_fields = ("title", "title_slug")


@admin.register(SubmissionLog)
class SubmissionLogAdmin(admin.ModelAdmin):
    list_display = ("user", "problem", "solved_at", "source")
    list_filter = ("source", "problem__difficulty")
    search_fields = ("user__username", "problem__title_slug")
    autocomplete_fields = ("user", "problem")
    date_hierarchy = "solved_at"
