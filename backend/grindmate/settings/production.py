"""Production settings - strict, secure, observable."""

from __future__ import annotations

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa: F403

DEBUG = False

# Force ALLOWED_HOSTS / SECRET_KEY to come from the environment in prod.
SECRET_KEY = env("DJANGO_SECRET_KEY")  # noqa: F405
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")  # noqa: F405

# Cross-origin POSTs from the React frontend trip CSRF unless its origin is
# trusted. List the full origin including scheme: https://your-app.vercel.app
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405

# --- Security headers ------------------------------------------
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# --- Observability ---------------------------------------------
SENTRY_DSN = env("SENTRY_DSN", default="")  # noqa: F405
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment=env("DJANGO_ENV", default="production"),  # noqa: F405
    )

# --- Logging overrides -----------------------------------------
LOGGING["loggers"]["apps"]["level"] = "INFO"  # noqa: F405
LOGGING["loggers"]["urllib3"] = {  # noqa: F405
    "handlers": ["console"],
    "level": "WARNING",
    "propagate": False,
}
LOGGING["loggers"]["requests"] = {  # noqa: F405
    "handlers": ["console"],
    "level": "WARNING",
    "propagate": False,
}

# --- Cache fallback --------------------------------------------
# If REDIS_URL is not configured in prod, use in-process cache rather than
# silently failing on a non-existent localhost Redis.
if not env("REDIS_URL", default=""):  # noqa: F405
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "grindmate-prod",
        },
    }
