import os
import re
import time
import tarfile
import datetime
from cStringIO import StringIO

from django.conf import settings
from django.db import reset_queries
from django.core.management.base import BaseCommand

from chronam.core.models import Batch

ocr_dumpfile_size = 1000 # number of pages per part-n.tar.bz2 file

class Command(BaseCommand):
    help = "creates bulk download files for page ocr text and xml"

    def handle(self, *args, **options):
        if not os.path.isdir(settings.OCR_DUMP_STORAGE):
            os.makedirs(settings.OCR_DUMP_STORAGE)

        now = time.time()
        count = 0
        tar = None

        for batch in Batch.objects.all():
            for issue in batch.issues.all():
                for page in issue.pages.all():
                    if not page.ocr_filename:
                        continue

                    # pages are split into tar files of a particular size
                    count += 1
                    if not tar or count >= ocr_dumpfile_size:
                        if tar: tar.close()
                        tar = next_tarfile()
                        print "writing to %s" % tar.name
                        count = 0

                    relative_dir = page_path(page)

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

            batch.ocr_dumped = datetime.datetime.fromtimestamp(now)
            batch.save()
            reset_queries()
        tar.close()

def page_path(page):
    d = page.issue.date_issued
    return "%s/%i/%02i/%02i/ed-%i/seq-%i/" %  (page.issue.title.lccn, d.year, d.month, d.day, page.issue.edition, page.sequence)

def next_tarfile():
    n = 0
    for f in os.listdir(settings.OCR_DUMP_STORAGE):
        m = re.match("^part-(\d+).tar.bz2$", f)
        if m and int(m.group(1)) > n:
            n = int(m.group(1))
    filename = "part-%05i.tar.bz2" % (n + 1)
    filename = os.path.join(settings.OCR_DUMP_STORAGE, filename)
    return tarfile.open(filename, 'w:bz2')
