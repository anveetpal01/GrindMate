"""Permissions for groups endpoints."""

from __future__ import annotations

from rest_framework import permissions

from .models import Group


class IsGroupMember(permissions.BasePermission):
    """User must be a member of the Group obj to access it."""

    message = "You are not a member of this group."

    def has_object_permission(self, request, view, obj: Group) -> bool:
        return obj.has_member(request.user)


class IsGroupAdmin(permissions.BasePermission):
    """User must be an admin (or owner) of the Group obj."""

    message = "Admin permission required for this group."

    def has_object_permission(self, request, view, obj: Group) -> bool:
        return obj.owner_id == request.user.id or obj.is_admin(request.user)
