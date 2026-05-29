"""URL routes for /api/v1/groups/."""

from django.urls import path

from . import views

app_name = "groups"

urlpatterns = [
    path("", views.GroupListCreateView.as_view(), name="list_create"),
    path("<uuid:public_id>/", views.GroupDetailView.as_view(), name="detail"),
    path("<uuid:public_id>/members/", views.GroupMembersView.as_view(), name="members"),
    path("<uuid:public_id>/leave/", views.LeaveGroupView.as_view(), name="leave"),
    path("<uuid:public_id>/invite/", views.GroupInviteView.as_view(), name="invite"),
    path("<uuid:public_id>/leaderboard/", views.LeaderboardView.as_view(), name="leaderboard"),
    path("join/<str:invite_token>/", views.JoinByInviteView.as_view(), name="join"),
]
