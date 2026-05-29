"""Django admin for the groups app."""

from __future__ import annotations

from django.contrib import admin

from .models import Group, GroupInvite, GroupMembership


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 0
    autocomplete_fields = ("user",)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")
    search_fields = ("name", "owner__username")
    autocomplete_fields = ("owner",)
    inlines = [GroupMembershipInline]
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(GroupInvite)
class GroupInviteAdmin(admin.ModelAdmin):
    list_display = ("group", "token", "expires_at", "use_count", "max_uses", "revoked")
    list_filter = ("revoked",)
    search_fields = ("group__name", "token")
    readonly_fields = ("token", "use_count", "created_at")


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ("group", "user", "role", "joined_at")
    list_filter = ("role",)
    search_fields = ("group__name", "user__username")
    autocomplete_fields = ("group", "user")
