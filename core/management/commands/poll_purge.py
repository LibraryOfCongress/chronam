from __future__ import absolute_import

import logging
import os

from django.core.management.base import BaseCommand, CommandError

from chronam.core import tasks

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "manual command to process purge_batch requests  from CTS"

    def handle(self, *args, **options):
        try:
            tasks.poll_purge.apply()
        except Exception as e:
            LOGGER.exception(e)
            raise CommandError("Unable to purge batches")
