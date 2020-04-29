from __future__ import absolute_import

import logging

from django.core.management.base import CommandError

from chronam.core import tasks

from . import LoggingCommand

LOGGER = logging.getLogger(__name__)


class Command(LoggingCommand):
    help = "manual command to process purge_batch requests from CTS"  # NOQA: A003

    def handle(self, *args, **options):
        try:
            tasks.poll_purge.apply()
        except Exception:
            LOGGER.exception("Unable to process purge_batch requests:")
            raise CommandError("Unable to purge batches")
