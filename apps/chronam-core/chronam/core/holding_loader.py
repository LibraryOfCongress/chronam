import logging
from time import time

from pymarc import map_xml
from django.db import reset_queries

from chronam.core.title_loader import _normal_oclc, _extract
from chronam.core import models

_logger = logging.getLogger(__name__)


class HoldingLoader:
    """
    A loader for holdings data. Intended to be run after titles have been
    loaded with TitleLoader. This is necessary so that holdings records
    can be attached to the appropriate Title.
    """

    def __init__(self):
        self.records_processed = 0
        self.missing_title = 0
        self.missing_institition = 0
        self.count = 0
        self.errors = 0

    def load_file(self, filename, skip=0):
        t0 = time()
        times = []

        def load_record(record):
            try:
                self.records_processed += 1
                if skip > self.records_processed:
                    _logger.info("skipped %i" % self.records_processed)
                    return
                if record.leader[6] == 'y':
                    self.load_holding(record)

            except Exception, e:
                _logger.error("unable to load record %s: %s" % (self.records_processed, e))
                _logger.exception(e)
                self.errors += 1

            seconds = time() - t0
            times.append(seconds)

            if self.records_processed % 1000 == 0:
                _logger.info("processed %sk records in %.2f seconds" % 
                             (self.records_processed/1000, seconds))

        map_xml(load_record, file(filename, "rb"))

    def load_holding(self, record):
        # get the oclc number to link to
        oclc = _normal_oclc(_extract(record, '004'))
        if not oclc:
            _logger.error("holding record missing title: record %s, oclc %s" % (self.records_processed, oclc))
            self.errors += 1
            return
        try:
            title = models.Title.objects.get(oclc=oclc)
        except models.Title.DoesNotExist:
            _logger.error("Holding missing Title to link to: record %s, oclc %s" % (self.records_processed, oclc))
            self.missing_title += 1
            self.errors += 1
            return
       
        # get the institution to link to
        inst_code = _extract(record, '852', 'a') 
        try:
            inst = models.Institution.objects.get(code=inst_code)
        except models.Institution.DoesNotExist:
            _logger.error("Holding missing Institution to link to: %s" %
                          inst_code)
            self.missing_institutions += 1
            self.errors += 1
            return

        # get the holdings type
        type = _holdings_type(_extract(record, '852', 't'))

        # get the description
        desc = _extract(record, '866', 'a') or _extract(record, '866', 'z')
        if not desc:
            _logger.error("missing description: record %s, oclc %s" % (self.records_processed, oclc))
            return 

        # get the last modified date
        f008 = _extract(record, '008')
        date = None
        if f008:
            y = int(f008[26:28])
            m = int(f008[28:30])
            # TODO: should this handle 2 digit years better?
            if y and m:
                if y < 10:
                    y = 2000 + y
                else:
                    y = 1900 + y
                date = "%02i/%i" % (m, y)

        # persist it
        holding = models.Holding(title=title, institution=inst,
                                 description=desc, type=type, last_updated=date)
        holding.save()
        reset_queries()

    def main(self, marcxml_file):
        loader = HoldingLoader()
        _logger.info("loading holdings from: %s" % marcxml_file)
        loader.load_file(marcxml_file)
        _logger.info("records processed: %i" % loader.records_processed)
        _logger.info("missing title: %i" % self.missing_title)
        _logger.info("missing institution: %i" % self.missing_institition)
        _logger.info("errors: %i" % loader.errors)

def _holdings_type(s):
    if s == "OR":
        return "Original"
    elif s == "FM":
        return "Microfilm Service Copy"
    elif s == "FMM":
        return "Microfilm Master"
    elif s == "FC":
        return "Microfiche Service Copy"
    elif s == "FCM":
        return "Microfiche Master"
    elif s == "OP":
         return "Microopaque Service Copy"
    elif s == "OPM":
         return "Microopaque Master"
    elif s == "RP":
         return "Eye-Readable Reprint"
    else:
        return None
