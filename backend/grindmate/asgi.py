"""ASGI entry point - for future websockets / async views."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "grindmate.settings.production")

application = get_asgi_application()
