import os
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from chronam.core.models import Batch, OcrDump

logging.basicConfig(filename="dump_ocr.log", level=logging.INFO)

class Command(BaseCommand):
    help = "looks for batches that need to have ocr dump files created"

    def handle(self, *args, **options):
        if not os.path.isdir(settings.OCR_DUMP_STORAGE):
            os.makedirs(settings.OCR_DUMP_STORAGE)

        for batch in Batch.objects.filter(ocr_dump__isnull=True):
            dump = OcrDump.new_from_batch(batch)
            logging.info("created ocr dump file: %s" % dump)
