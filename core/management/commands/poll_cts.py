import os
import logging

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from openoni.core.management.commands import configure_logging
from openoni.core import tasks
    
configure_logging('poll_cts_logging.config', 
                  'poll_cts_%s.log' % os.getpid())

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "manual command to load new batches from cts"

    def handle(self, *args, **options):
        try:
            tasks.poll_cts.apply()
        except Exception, e:
            log.exception(e)
            raise CommandError("unable to load batches from cts")
