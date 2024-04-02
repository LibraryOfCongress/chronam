import datetime
import logging
import os

from celery.schedules import crontab

from chronam.settings import *  # NOQA
from chronam.settings import INSTALLED_APPS

APP_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


CELERY_IMPORTS = ("chronam.core.tasks",)
CELERYD_LOG_FILE = os.path.join("/var/log/celery", "celery.log")
CELERYD_LOG_LEVEL = logging.INFO
CELERYD_CONCURRENCY = 2

CELERYBEAT_SCHEDULE = {
    "delete_django_cache": {
        "task": "chronam.core.tasks.delete_django_cache",
        "schedule": crontab(hour=5, minute=0),
    },
}

if "chronam.loc_cts" in INSTALLED_APPS:
    CELERY_IMPORTS += ("chronam.loc_cts.tasks",)
    CELERYBEAT_SCHEDULE["poll_cts"] = {
        "task": "chronam.loc_cts.tasks.poll_cts",
        "schedule": datetime.timedelta(hours=1),
        "args": (),
    }

    CELERYBEAT_SCHEDULE["poll_purge"] = {
        "task": "chronam.loc_cts.tasks.poll_purge",
        "schedule": crontab(hour=3, minute=0),
        "args": (),
    }


CELERYBEAT_LOG_FILE = os.path.join("/var/log/celery", "celerybeat.log")
CELERYBEAT_LOG_LEVEL = logging.INFO
