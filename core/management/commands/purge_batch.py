from __future__ import absolute_import

import logging

from django.core.management.base import CommandError

from chronam.core.batch_loader import BatchLoader, BatchLoaderException

from . import LoggingCommand

LOGGER = logging.getLogger(__name__)


class Command(LoggingCommand):
    help = "Purge a batch"  # NOQA: A003
    args = "<batch_name>"

    def handle(self, batch_name=None, *args, **options):
        if len(args) != 0:
            raise CommandError("Usage is purge_batch %s" % self.args)

        loader = BatchLoader()
        try:
            LOGGER.info("purging batch %s", batch_name)
            loader.purge_batch(batch_name)
        except BatchLoaderException:
            LOGGER.exception("Unable to purge batch %s", batch_name)
            raise CommandError("unable to purge batch. check the log for clues")
