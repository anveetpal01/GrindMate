"""Group + leaderboard endpoints."""

from __future__ import annotations

from dataclasses import asdict

from django.db import transaction
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .leaderboard import compute_leaderboard
from .models import Group, GroupInvite, GroupMembership
from .permissions import IsGroupAdmin, IsGroupMember
from .serializers import (
    GroupInviteSerializer,
    GroupMembershipSerializer,
    GroupSerializer,
    LeaderboardRowSerializer,
)


class GroupListCreateView(generics.ListCreateAPIView):
    """GET - groups the current user is in.
    POST - create a new group; the creator becomes owner + admin member.
    """

    serializer_class = GroupSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = "public_id"

    def get_queryset(self):
        return (
            Group.objects.filter(memberships__user=self.request.user)
            .annotate(member_count=Count("memberships"))
            .prefetch_related(
                Prefetch(
                    "memberships",
                    queryset=GroupMembership.objects.filter(user=self.request.user),
                ),
            )
            .order_by("-created_at")
        )

    @transaction.atomic
    def perform_create(self, serializer):
        group = serializer.save(owner=self.request.user)
        GroupMembership.objects.create(
            group=group,
            user=self.request.user,
            role=GroupMembership.ROLE_ADMIN,
        )


class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE a single group. Member to read, admin to update/delete."""

    serializer_class = GroupSerializer
    lookup_field = "public_id"

    def get_queryset(self):
        return Group.objects.annotate(member_count=Count("memberships")).prefetch_related(
            "memberships__user"
        )

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated(), IsGroupMember()]
        return [permissions.IsAuthenticated(), IsGroupAdmin()]


class GroupMembersView(generics.ListAPIView):
    """GET /api/v1/groups/<public_id>/members/."""

    serializer_class = GroupMembershipSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated(), IsGroupMember()]

    def get_queryset(self):
        group = get_object_or_404(Group, public_id=self.kwargs["public_id"])
        # Object-level perm check fires via filter_queryset's permission machinery.
        self.check_object_permissions(self.request, group)
        return group.memberships.select_related("user").order_by("-role", "user__username")


class LeaveGroupView(APIView):
    """DELETE /api/v1/groups/<public_id>/leave/."""

    permission_classes = (permissions.IsAuthenticated,)

    def delete(self, request, public_id):
        group = get_object_or_404(Group, public_id=public_id)
        membership = group.memberships.filter(user=request.user).first()
        if not membership:
            return Response({"detail": "Not a member."}, status=status.HTTP_404_NOT_FOUND)
        if group.owner_id == request.user.id:
            raise ValidationError("Owner cannot leave; transfer ownership or delete the group.")
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GroupInviteView(APIView):
    """POST /api/v1/groups/<public_id>/invite/ - generate a fresh invite token."""

    def get_permissions(self):
        return [permissions.IsAuthenticated(), IsGroupAdmin()]

    def post(self, request, public_id):
        group = get_object_or_404(Group, public_id=public_id)
        self.check_object_permissions(request, group)

        invite = GroupInvite.objects.create(
            group=group,
            created_by=request.user,
            max_uses=request.data.get("max_uses"),
        )
        return Response(
            GroupInviteSerializer(invite).data,
            status=status.HTTP_201_CREATED,
        )


class JoinByInviteView(APIView):
    """POST /api/v1/groups/join/<invite_token>/."""

    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def post(self, request, invite_token):
        try:
            invite = (
                GroupInvite.objects.select_related("group")
                .select_for_update()
                .get(token=invite_token)
            )
        except GroupInvite.DoesNotExist:
            return Response({"detail": "Invalid invite."}, status=status.HTTP_404_NOT_FOUND)

        if not invite.is_active():
            return Response(
                {"detail": "Invite expired or fully used."},
                status=status.HTTP_410_GONE,
            )

        membership, created = GroupMembership.objects.get_or_create(
            group=invite.group,
            user=request.user,
            defaults={"role": GroupMembership.ROLE_MEMBER},
        )
        if created:
            invite.consume()

        return Response(
            GroupSerializer(invite.group, context={"request": request}).data,
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED,
        )


class LeaderboardView(APIView):
    """GET /api/v1/groups/<public_id>/leaderboard/?period=daily|weekly|all-time."""

    def get_permissions(self):
        return [permissions.IsAuthenticated(), IsGroupMember()]

    def get(self, request, public_id):
        group = get_object_or_404(Group, public_id=public_id)
        self.check_object_permissions(request, group)

        period = request.query_params.get("period", "weekly")
        if period not in ("daily", "weekly", "all-time"):
            raise ValidationError({"period": "Must be 'daily', 'weekly', or 'all-time'."})

        rows = compute_leaderboard(group, period)
        data = LeaderboardRowSerializer([asdict(r) for r in rows], many=True).data
        return Response({"period": period, "rows": data})
