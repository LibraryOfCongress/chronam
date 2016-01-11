import os
import logging

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from openoni.core.management.commands import configure_logging
from openoni.core import tasks

configure_logging('queue_process_coordinates.config',
                  'queue_process_coordinates_%s.log' % os.getpid())

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
    )
    help = "queue the word coordinates of a batch to be processed"
    args = '<batch name>'

    def handle(self, batch_name, *args, **options):
        if len(args)!=0:
            raise CommandError('Usage is queue_process_coordinates %s' % self.args)
        try:
            tasks.process_coordinates.delay(batch_name)
        except Exception, e:
            LOGGER.exception(e)
            raise CommandError("unable to process coordinates. check the queue_load_batch log for clues")
