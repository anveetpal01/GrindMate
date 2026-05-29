"""Development settings - local-friendly defaults, more verbose logging."""

from .base import *  # noqa: F403

DEBUG = True

INSTALLED_APPS += ["django_extensions"]  # type: ignore[name-defined]  # noqa: F405

# Friendly defaults - override via .env when needed.
ALLOWED_HOSTS = ["*"]
INTERNAL_IPS = ["127.0.0.1", "localhost"]

# Loosen CORS in dev - the Vite proxy + browsers are picky.
CORS_ALLOW_ALL_ORIGINS = True

# Console emails so we can see verification links during signup.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Default to in-memory cache so devs don't need Redis to run the API.
# Set DJANGO_DEV_USE_REDIS=1 in .env when you want to exercise Redis caching.
if not env.bool("DJANGO_DEV_USE_REDIS", default=False):  # noqa: F405
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "grindmate-dev",
        },
    }

# Eager Celery in dev makes integration testing painless.
# Set CELERY_TASK_ALWAYS_EAGER=False in .env to test real workers.
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=True)  # noqa: F405
CELERY_TASK_EAGER_PROPAGATES = True

LOGGING["root"]["level"] = "DEBUG"  # type: ignore[index]  # noqa: F405
