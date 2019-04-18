from __future__ import absolute_import

import logging
import os
from optparse import make_option

from django.conf import settings

from chronam.core.models import Batch, OcrDump

from . import LoggingCommand


class Command(LoggingCommand):
    help = 'dump OCR for one or more batches'  # NOQA:A003
    args = '<batch name>'

    option_list = LoggingCommand.option_list + (
        make_option('--overwrite', action='store_true', default=False, help='Replace existing OCR dumps'),
    )

    def handle(self, *args, **options):
        overwrite = options['overwrite']

        if not os.path.isdir(settings.OCR_DUMP_STORAGE):
            os.makedirs(settings.OCR_DUMP_STORAGE)

        for batch_name in args:
            batch = Batch.objects.get(name=batch_name)
            logging.info('Starting to dump OCR for batch %s', batch_name)

            if hasattr(batch, 'ocr_dump'):
                if overwrite:
                    logging.info('Deleting existing dump file %s before recreating it', batch.ocr_dump.path)
                    batch.ocr_dump.delete()
                else:
                    logging.warning(
                        'Skipping batch %s because dump %s exists and --overwrite was not specified',
                        batch_name,
                        batch.ocr_dump.path,
                    )
                    continue

            dump = OcrDump.new_from_batch(batch)
            logging.info('Created OCR dump for batch %s: %s', batch_name, dump)
