from django.apps import AppConfig


class LeetcodeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.leetcode"
    label = "leetcode"
    verbose_name = "LeetCode integration"

    def ready(self) -> None:
        from . import signals  # noqa: F401  - register handlers
