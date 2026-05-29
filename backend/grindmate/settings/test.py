"""Test settings - fast, in-memory, no external services."""

from .base import *  # noqa: F403

# In-memory SQLite for speed.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Don't hash passwords during tests - speeds up factory_boy user creation.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# In-memory cache so tests don't need Redis.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Run Celery tasks synchronously, no broker needed.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Effectively disable throttling in tests by setting astronomically high rates.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100000/hour",
        "user": "100000/hour",
        "register": "100000/hour",
        "verify_email": "100000/hour",
        "password_reset": "100000/hour",
        "resend_verification": "100000/hour",
    },
}
