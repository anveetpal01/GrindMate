"""LeetCode API endpoints.

GET    /api/v1/leetcode/account/             current user's LeetCodeAccount
POST   /api/v1/leetcode/account/             link/replace handle
DELETE /api/v1/leetcode/account/             unlink
POST   /api/v1/leetcode/account/sync/        trigger manual sync (sync, not Celery)
GET    /api/v1/leetcode/submissions/         list current user's solves (paginated)
POST   /api/v1/leetcode/submissions/manual/  manually mark a problem solved
"""

from __future__ import annotations

import logging
import secrets

from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LeetCodeAccount, SubmissionLog, SyncStatus
from .serializers import (
    LeetCodeAccountSerializer,
    ManualSubmissionSerializer,
    SubmissionLogSerializer,
)
from .services import LeetCodeAPIError
from .sync import backfill_problem_meta, sync_account, upsert_problem, verify_account

logger = logging.getLogger(__name__)


class LeetCodeAccountView(APIView):
    """Manage the current user's LeetCode handle."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        account = LeetCodeAccount.objects.filter(user=request.user).first()
        if not account:
            return Response(
                {"detail": "No LeetCode account linked."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(LeetCodeAccountSerializer(account).data)

    def post(self, request):
        serializer = LeetCodeAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        handle = serializer.validated_data["handle"]

        account, created = LeetCodeAccount.objects.update_or_create(
            user=request.user,
            defaults={"handle": handle, "sync_status": SyncStatus.PENDING},
        )

        # Fast verification: single profile fetch (~2s). Recent solves come in
        # via the scheduled cron or an explicit /account/sync/ call later, so
        # the link endpoint stays under any reasonable HTTP timeout.
        result = verify_account(account)
        if result.error:
            return Response(
                {
                    "detail": f"Handle linked but verification failed. Reason: {result.error}",
                    "account": LeetCodeAccountSerializer(account).data,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        return Response(
            LeetCodeAccountSerializer(account).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request):
        deleted, _ = LeetCodeAccount.objects.filter(user=request.user).delete()
        if not deleted:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SyncAccountView(APIView):
    """Trigger a synchronous sync for the current user's LeetCode handle."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        account = LeetCodeAccount.objects.filter(user=request.user).first()
        if not account:
            return Response(
                {"detail": "No LeetCode account linked yet."},
                status=status.HTTP_404_NOT_FOUND,
            )

        result = sync_account(account)
        return Response(
            {
                "new_solves": result.new_solves,
                "total_solved": result.total_solved,
                "problems_resolved": result.problems_resolved,
                "error": result.error,
                "account": LeetCodeAccountSerializer(account).data,
            }
        )


class SubmissionListView(generics.ListAPIView):
    serializer_class = SubmissionLogSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_fields = ("source", "problem__difficulty")

    def get_queryset(self):
        return (
            SubmissionLog.objects.filter(user=self.request.user)
            .select_related("problem")
            .order_by("-solved_at")
        )


class CronSyncAllView(APIView):
    """POST /api/v1/leetcode/cron/sync-all/ - run a sync for every linked account.

    Protected by a shared secret instead of JWT, because it's invoked by an
    external scheduler (GitHub Actions) without a user session. The secret
    must match `settings.CRON_SHARED_SECRET` and arrive in `X-Cron-Token`.
    """

    permission_classes = (permissions.AllowAny,)
    throttle_classes = ()  # external scheduler should not be throttled

    def post(self, request):
        expected = settings.CRON_SHARED_SECRET
        if not expected:
            return Response(
                {"detail": "Cron sync is disabled (CRON_SHARED_SECRET not set)."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        provided = request.headers.get("X-Cron-Token", "")
        if not secrets.compare_digest(provided.encode(), expected.encode()):
            return Response(
                {"detail": "Invalid token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        accounts = list(
            LeetCodeAccount.objects.exclude(sync_status=SyncStatus.UNVERIFIED),
        )
        synced = 0
        failed = 0
        for account in accounts:
            result = sync_account(account)
            if result.error:
                failed += 1
            else:
                synced += 1

        logger.info("Cron sync done: %d ok, %d failed", synced, failed)
        return Response({"synced": synced, "failed": failed, "total": len(accounts)})


class CronBackfillProblemsView(APIView):
    """POST /api/v1/leetcode/cron/backfill-problems/

    Fills in Problem rows that were created with a placeholder difficulty by
    the deferred sync path. Capped at `limit` per invocation so the request
    fits inside the worker timeout. Same shared-secret gating as CronSyncAllView.
    """

    permission_classes = (permissions.AllowAny,)
    throttle_classes = ()

    DEFAULT_LIMIT = 30

    def post(self, request):
        from .models import Problem
        from .services import LeetCodeClient

        expected = settings.CRON_SHARED_SECRET
        if not expected:
            return Response(
                {"detail": "Cron sync is disabled (CRON_SHARED_SECRET not set)."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        provided = request.headers.get("X-Cron-Token", "")
        if not secrets.compare_digest(provided.encode(), expected.encode()):
            return Response(
                {"detail": "Invalid token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            limit = int(request.query_params.get("limit", self.DEFAULT_LIMIT))
        except ValueError:
            limit = self.DEFAULT_LIMIT
        limit = max(1, min(limit, 100))

        pending = list(
            Problem.objects.filter(difficulty="").values_list("title_slug", flat=True)[:limit]
        )
        if not pending:
            return Response({"backfilled": 0, "failed": 0, "total": 0})

        client = LeetCodeClient()
        backfilled = 0
        failed = 0
        for slug in pending:
            try:
                backfill_problem_meta(slug, client=client)
                backfilled += 1
            except LeetCodeAPIError as exc:
                logger.info("Backfill skipped slug=%s: %s", slug, exc)
                failed += 1

        logger.info(
            "Backfill done: %d ok, %d failed, %d remaining-batch", backfilled, failed, len(pending)
        )
        return Response({"backfilled": backfilled, "failed": failed, "total": len(pending)})


class ManualSubmissionView(APIView):
    """Manually mark a problem as solved - fallback when auto-sync fails."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = ManualSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        slug = serializer.validated_data["title_slug"]
        solved_at = serializer.validated_data.get("solved_at") or timezone.now()

        try:
            problem = upsert_problem(slug)
        except LeetCodeAPIError as exc:
            return Response(
                {"detail": f"Could not resolve problem: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            log = SubmissionLog.objects.create(
                user=request.user,
                problem=problem,
                solved_at=solved_at,
                source=SubmissionLog.SOURCE_MANUAL,
            )
        except IntegrityError:
            return Response(
                {"detail": "You already logged this solve at that timestamp."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(SubmissionLogSerializer(log).data, status=status.HTTP_201_CREATED)
