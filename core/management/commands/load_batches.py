import os
import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from chronam.core import batch_loader

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--skip-process-ocr', 
                    action='store_false', 
                    dest='process_ocr', default=True,
                    help='Do not generate ocr, and index'),
        make_option('--skip-process-coordinates', 
                    action='store_false', 
                    dest='process_coordinates', default=True,
                    help='Do not write out word coordinates'),
    )
    help = "Load batches by name from a batch list file"
    args = '<batch_list_filename>'

    def handle(self, batch_list_filename, *args, **options):
        if len(args) != 0:
            raise CommandError('Usage is load_batch %s' % self.args)

        loader = batch_loader.BatchLoader()
        loader.PROCESS_OCR = options['process_ocr']
        loader.PROCESS_COORDINATES = options['process_coordinates']

        batch_list = file(batch_list_filename)
        LOGGER.info("batch_list_filename: %s" % batch_list_filename)
        for line in batch_list:
            batch_name = line.strip()
            LOGGER.info("batch_name: %s" % batch_name)
            loader.load_batch(batch_name, strict=False)
