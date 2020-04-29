import logging
import os

from celery.schedules import crontab

from chronam.settings import *  # NOQA

APP_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


CELERY_IMPORTS = ("chronam.core.tasks",)
CELERYD_LOG_FILE = os.path.join("/logs/celery", "celery.log")
CELERYD_LOG_LEVEL = logging.INFO
CELERYD_CONCURRENCY = 2

CELERYBEAT_SCHEDULE = {
    "poll_cts": {
        "task": "chronam.core.tasks.poll_cts",
        "schedule": datetime.timedelta(hours=4),
        "args": ()
    },
    "load_essays": {
        "task": "chronam.core.tasks.load_essays",
        "schedule": crontab(hour=0, minute=0),
        "args": (),
    },
    "delete_django_cache": {
        "task": "chronam.core.tasks.delete_django_cache",
        "schedule": crontab(hour=5, minute=0),
    },
}

CELERYBEAT_LOG_FILE = os.path.join("/var/log/celery", "celerybeat.log")
CELERYBEAT_LOG_LEVEL = logging.INFO
