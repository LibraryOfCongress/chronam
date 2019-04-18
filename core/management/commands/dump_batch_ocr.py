from __future__ import absolute_import

import logging
import os

from django.conf import settings

from chronam.core.models import Batch, OcrDump

from . import LoggingCommand

LOGGER = logging.getLogger(__name__)


class Command(LoggingCommand):
    help = "dump ocr for a single batch"
    args = '<batch name>'

    def handle(self, batch_name, *args, **options):
        if not os.path.isdir(settings.OCR_DUMP_STORAGE):
            os.makedirs(settings.OCR_DUMP_STORAGE)

        batch = Batch.objects.get(name=batch_name)
        LOGGER.info("starting to dump ocr for %s", batch)
        dump = OcrDump.new_from_batch(batch)
        LOGGER.info("created ocr dump %s for %s", dump, batch)
