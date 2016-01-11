import os

from django.conf import settings
from django.core.management.base import BaseCommand

from openoni.core.models import Batch
from openoni.core.tasks import dump_ocr

class Command(BaseCommand):
    help = "looks for batches that need to have ocr dump files created"

    def handle(self, *args, **options):
        if not os.path.isdir(settings.OCR_DUMP_STORAGE):
            os.makedirs(settings.OCR_DUMP_STORAGE)

        for batch in Batch.objects.filter(ocr_dump__isnull=True):
            print "queueing %s for ocr dump" % batch
            dump_ocr.delay(batch.name)
