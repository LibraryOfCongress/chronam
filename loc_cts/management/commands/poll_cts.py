from __future__ import absolute_import

import logging

from django.core.management.base import CommandError

from chronam.loc_cts.tasks import poll_cts

from . import LoggingCommand

LOGGER = logging.getLogger(__name__)


class Command(LoggingCommand):
    help = "manual command to load new batches from CTS"  # NOQA: A003

    def handle(self, *args, **options):
        try:
            poll_cts.apply()
        except Exception:
            LOGGER.exception("Unable to load new batches from CTS")
            raise CommandError("unable to load batches from CTS")
