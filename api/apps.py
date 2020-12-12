from django.apps import AppConfig


class DefaultConfig(AppConfig):
    name = "api"

    def ready(self):
        # importing singnals to register them
        from .signals import profile  # noqa: F401
