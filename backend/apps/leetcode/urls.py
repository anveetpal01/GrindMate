"""URL routes for /api/v1/leetcode/."""

from django.urls import path

from . import views

app_name = "leetcode"

urlpatterns = [
    path("account/", views.LeetCodeAccountView.as_view(), name="account"),
    path("account/sync/", views.SyncAccountView.as_view(), name="account_sync"),
    path("submissions/", views.SubmissionListView.as_view(), name="submissions"),
    path("submissions/manual/", views.ManualSubmissionView.as_view(), name="submissions_manual"),
    path("cron/sync-all/", views.CronSyncAllView.as_view(), name="cron_sync_all"),
    path(
        "cron/backfill-problems/",
        views.CronBackfillProblemsView.as_view(),
        name="cron_backfill_problems",
    ),
]
