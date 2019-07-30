from __future__ import absolute_import, print_function

import os

from django.conf import settings

from chronam.core.models import Batch
from chronam.core.tasks import dump_ocr

from . import LoggingCommand


class Command(LoggingCommand):
    help = "looks for batches that need to have ocr dump files created"  # NOQA: A003

    def handle(self, *args, **options):
        if not os.path.isdir(settings.OCR_DUMP_STORAGE):
            os.makedirs(settings.OCR_DUMP_STORAGE)

        for batch in Batch.objects.filter(ocr_dump__isnull=True):
            self.stdout.write(u"queueing %s for ocr dump" % batch)
            dump_ocr.delay(batch)
