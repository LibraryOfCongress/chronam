from __future__ import absolute_import

import logging
import os

from django.conf import settings

from chronam.core.models import Batch, OcrDump

from . import LoggingCommand


class Command(LoggingCommand):
    help = "dump OCR for one or more batches"
    args = '<batch name>'

    def handle(self, *args, **options):
        if not os.path.isdir(settings.OCR_DUMP_STORAGE):
            os.makedirs(settings.OCR_DUMP_STORAGE)

        for batch_name in args:
            batch = Batch.objects.get(name=batch_name)
            logging.info("Starting to dump OCR for batch %s", batch_name)
            dump = OcrDump.new_from_batch(batch)
            logging.info("Created OCR dump for batch %s in %s", batch_name, dump)
