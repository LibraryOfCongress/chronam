import os
import time
import tarfile
from cStringIO import StringIO

from django.conf import settings
from django.db import reset_queries
from django.core.management.base import BaseCommand

from chronam.core.models import Batch

class Command(BaseCommand):
    help = "creates bulk download files for page ocr text and xml"

    def handle(self, *args, **options):
        if not os.path.isdir(settings.OCR_DUMP_STORAGE):
            os.makedirs(settings.OCR_DUMP_STORAGE)

        now = time.time()
        tarfilename = os.path.join(settings.OCR_DUMP_STORAGE, "part_000001.tar.bz2")
        tar = tarfile.open(tarfilename, 'w:bz2')
        for batch in Batch.objects.all():
            for issue in batch.issues.all():
                for page in issue.pages.all():
                    if not page.ocr_filename:
                        continue
                    relative_dir = page.url.lstrip("/")

                    # add ocr text
                    txt_filename = relative_dir + "ocr.txt"
                    ocr_text = page.ocr.text.encode('utf-8')
                    info = tarfile.TarInfo(name=txt_filename)
                    info.size = len(ocr_text)
                    info.mtime = now 
                    tar.addfile(info, StringIO(ocr_text))
                    print txt_filename

                    # add ocr xml
                    xml_filename = relative_dir + "ocr.xml"
                    info = tarfile.TarInfo(name=xml_filename)
                    info.size = os.path.getsize(page.ocr_abs_filename)
                    info.mtime = now
                    tar.addfile(info, open(page.ocr_abs_filename))
                    print xml_filename

            reset_queries()
        tar.close()

