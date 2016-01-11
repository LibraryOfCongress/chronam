import os
import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from openoni.core.management.commands import configure_logging
from openoni.core import tasks
    
configure_logging('queue_load_batch_logging.config', 
                  'queue_load_batch_%s.log' % os.getpid())

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--skip-coordinates',
                     action='store_false',
                     dest='process_coordinates',
                     default=True,
                     help="Do not generate word coordinates"),
    )
    help = "queue a batch to be loaded"
    args = '<batch name>'

    def handle(self, batch_name, *args, **options):
        if len(args)!=0:
            raise CommandError('Usage is queue_load_batch %s' % self.args)
        try:
            tasks.load_batch.delay(batch_name, process_coordinates=options['process_coordinates'])
        except Exception, e:
            LOGGER.exception(e)
            raise CommandError("unable to queue load batch. check the queue_load_batch log for clues")
