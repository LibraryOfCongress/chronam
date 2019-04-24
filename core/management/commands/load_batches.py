from __future__ import absolute_import

from optparse import make_option

from django.core.management.base import CommandError

from chronam.core import batch_loader

from . import LoggingCommand


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
            '--skip-process-coordinates',
            action='store_false',
            dest='process_coordinates',
            default=True,
            help='Do not write out word coordinates',
        ),
    )
    help = "Load batches by name from a batch list file"  # NOQA: A003
    args = '<batch_list_filename>'

    def handle(self, batch_list_filename, *args, **options):
        if len(args) != 0:
            raise CommandError('Usage is load_batch %s' % self.args)

        loader = batch_loader.BatchLoader()
        loader.PROCESS_OCR = options['process_ocr']
        loader.PROCESS_COORDINATES = options['process_coordinates']

        batch_list = open(batch_list_filename)
        self.stdout.write("batch_list_filename: %s" % batch_list_filename)
        for line in batch_list:
            batch_name = line.strip()
            self.stdout.write("batch_name: %s" % batch_name)
            loader.load_batch(batch_name, strict=False)
