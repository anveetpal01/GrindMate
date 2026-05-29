"""Importing the Celery app here ensures shared_task discovers it on Django startup."""

from .celery import app as celery_app

__all__ = ("celery_app",)
