"""Django admin for users app."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import EmailVerificationToken, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("-date_joined",)
    list_display = (
        "username",
        "email",
        "display_name",
        "is_email_verified",
        "is_staff",
        "date_joined",
    )
    list_filter = ("is_email_verified", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email", "display_name")
    readonly_fields = ("public_id", "last_login", "date_joined", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Profile", {"fields": ("display_name", "avatar_url", "timezone")}),
        ("Verification", {"fields": ("is_email_verified",)}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (
            "System",
            {"fields": ("public_id", "last_login", "date_joined", "created_at", "updated_at")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "password1", "password2"),
            },
        ),
    )


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "created_at", "used_at")
    search_fields = ("user__email", "user__username", "token")
    readonly_fields = ("token", "created_at", "used_at")
