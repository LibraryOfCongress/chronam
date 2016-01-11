import os
import logging

from optparse import make_option

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from openoni.core.batch_loader import BatchLoader, BatchLoaderException
from openoni.core.management.commands import configure_logging
    
configure_logging('load_batch_logging.config', 
                  'load_batch_%s.log' % os.getpid())

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--skip-process-ocr', 
                    action='store_false', 
                    dest='process_ocr', default=True,
                    help='Do not generate ocr, and index'),
        make_option('--skip-coordinates', 
                    action='store_false', 
                    dest='process_coordinates', default=True,
                    help='Do not out word coordinates'),
    )
    help = "Load a batch"
    args = '<batch name>'

    def handle(self, batch_name, *args, **options):
        if len(args)!=0:
            raise CommandError('Usage is load_batch %s' % self.args)

        loader = BatchLoader(process_ocr=options['process_ocr'],
                             process_coordinates=options['process_coordinates'])
        try:
            batch = loader.load_batch(batch_name)
        except BatchLoaderException, e:
            LOGGER.exception(e)
            raise CommandError("unable to load batch. check the load_batch log for clues")
