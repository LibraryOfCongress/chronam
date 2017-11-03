import os
import logging

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from chronam.core import tasks
    
_logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "manual command to load new batches from cts"

    def handle(self, *args, **options):
        try:
            tasks.poll_cts.apply()
        except Exception, e:
            _logger.exception(e)
            raise CommandError("unable to load batches from cts")
