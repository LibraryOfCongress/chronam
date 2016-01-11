import os
import logging

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from openoni.core.management.commands import configure_logging
from openoni.core import tasks
    
configure_logging('queue_purge_batch_logging.config', 
                  'queue_purge_batch_%s.log' % os.getpid())

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
    )
    help = "queue a batch to be purged"
    args = '<batch name>'

    def handle(self, batch_name, *args, **options):
        if len(args)!=0:
            raise CommandError('Usage is queue_purge_batch %s' % self.args)
        try:
            tasks.purge_batch.delay(batch_name)
        except Exception, e:
            LOGGER.exception(e)
            raise CommandError("unable to queue purge batch. check the queue_purge_batch log for clues")

