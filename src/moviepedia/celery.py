import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "moviepedia.settings")

app = Celery("moviepedia")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.beat_schedule = {
    "daily-updateengagementscore": {
        "task": "api.tasks.run_management",
        "schedule": crontab(
            minute="0",
            hour="*/3",
        ),
        "args": ("updateengagementscore",),
    },
    "daily-updatepopscore": {
        "task": "api.tasks.run_management",
        "schedule": crontab(
            minute="3",
            hour="*/3",
        ),
        "args": ("updatepopscore",),
    },
    "daily-updateroles": {
        "task": "api.tasks.run_management",
        "schedule": crontab(
            minute="6",
            hour="*/3",
        ),
        "args": ("updateroles",),
    },
    "daily-updatetopcreators": {
        "task": "api.tasks.run_management",
        "schedule": crontab(
            minute="9",
            hour="*/3",
        ),
        "args": ("updatetopcreators",),
    },
    "daily-updatetopcurators": {
        "task": "api.tasks.run_management",
        "schedule": crontab(
            minute="12",
            hour="*/3",
        ),
        "args": ("updatetopcurators",),
    },
    "daily-updatemovierecommends": {
        "task": "api.tasks.run_management",
        "schedule": crontab(
            minute="15",
            hour="*/3",
        ),
        "args": ("updatemovierecommends",),
    },
    "daily-youtubelinkfix": {
        "task": "api.tasks.run_management",
        "schedule": crontab(
            minute="0",
            hour="3",
        ),
        "args": ("youtubelinkfix",),
    },
}

# Load task modules from all registered Django apps.
app.autodiscover_tasks()
