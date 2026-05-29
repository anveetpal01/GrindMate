"""Project-level URL routing.

API surface lives under /api/v1/. Versioning gives us a sane upgrade path.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def healthcheck(_request):
    """Liveness probe - used by Railway/Render and CI."""
    return JsonResponse({"status": "ok"})


api_v1_patterns = [
    path("auth/", include("apps.users.urls")),
    path("leetcode/", include("apps.leetcode.urls")),
    path("groups/", include("apps.groups.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", healthcheck, name="healthcheck"),
    path("api/v1/", include((api_v1_patterns, "v1"), namespace="v1")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
