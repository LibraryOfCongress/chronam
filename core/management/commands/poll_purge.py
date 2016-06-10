import os
import logging

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from chronam.core.management.commands import configure_logging
from chronam.core import tasks

configure_logging('poll_purge_logging.config',
                  'poll_purge_%s.log' % os.getpid())

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "manual command to process purge_batch requests  from CTS"

    def handle(self, *args, **options):
        try:
            tasks.poll_purge.apply()
        except Exception, e:
            log.exception(e)
            raise CommandError("Unable to purge batches")