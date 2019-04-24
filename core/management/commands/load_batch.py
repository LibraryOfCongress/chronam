from __future__ import absolute_import

import logging
from optparse import make_option

from django.core.management.base import CommandError

from chronam.core.batch_loader import BatchLoader, BatchLoaderException

from . import LoggingCommand

LOGGER = logging.getLogger(__name__)


class Command(LoggingCommand):
    option_list = LoggingCommand.option_list + (
        make_option(
            '--skip-process-ocr',
            action='store_false',
            dest='process_ocr',
            default=True,
            help='Do not generate ocr, and index',
        ),
        make_option(
            '--skip-coordinates',
            action='store_false',
            dest='process_coordinates',
            default=True,
            help='Do not out word coordinates',
        ),
    )
    help = "Load a batch"  # NOQA: A003
    args = '<batch name>'

    def handle(self, batch_name, *args, **options):
        if len(args) != 0:
            raise CommandError('Usage is load_batch %s' % self.args)

        loader = BatchLoader(
            process_ocr=options['process_ocr'], process_coordinates=options['process_coordinates']
        )
        try:
            loader.load_batch(batch_name)
        except BatchLoaderException as e:
            LOGGER.exception(e)
            raise CommandError("unable to load batch. check the load_batch log for clues")
