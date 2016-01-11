import logging
import os
from datetime import datetime
from time import time

from pymarc import map_xml
from django.db import reset_queries

from openoni.core.title_loader import _normal_oclc, _extract
from openoni.core import models

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
        self.errors = 0
        self.skipped = 0

        self.holding_created = 0
        self.no_oclc = 0
        self.files_processed = 0

    def load_file(self, filename, skip=0):
        t0 = time()
        times = []

        def _process_time():
            seconds = time() - t0
            times.append(seconds)

            if self.records_processed % 1000 == 0:
                _logger.info("processed %sk records in %.2f seconds" %
                             (self.records_processed / 1000, seconds))

        def load_xml_record(record):
            try:
                self.records_processed += 1
                if skip > self.records_processed:
                    _logger.info("skipped %i" % self.records_processed)
                    return
                if record.leader[6] == 'y':
                    self.load_xml_holding(record)

            except Exception, e:
                _logger.error("unable to load record %s: %s" %
                              (self.records_processed, e))
                _logger.exception(e)
                self.errors += 1

            _process_time()

        map_xml(load_xml_record, file(filename, "rb"))

    def _get_related_title(self, oclc):
        '''
        Match the title via oclc number or record an error.
        '''
        try:
            titles = models.Title.objects.filter(oclc=oclc)
            return titles
        except models.Title.DoesNotExist:
            _logger.error("Holding missing Title to link: record %s, oclc %s" %
                          (self.records_processed, oclc))
            self.missing_title += 1
            self.errors += 1
            return None

    def _get_related_inst_code(self, inst_code):
        ''' Match the institutional code or record an error.'''
        try:
            inst = models.Institution.objects.get(code=inst_code)
            return inst
        except models.Institution.DoesNotExist:
            _logger.error("Holding missing Institution to link to: %s" %
                          inst_code)
            self.errors += 1
            return None

    def _extract_holdings_type(self, record):
        ''' Extract holdings type from 007 field & 856 $u field. '''
        h856u = _extract(record, '856', 'u')
        if h856u and h856u.startswith('http://'):
            h_type = 'Online Resource'
        else:
            h_type = _holdings_type(_extract(record, '007'))
        return h_type

    def _parse_date(self, f008):
        '''
        Parse date takes the f008 field and pulls out the date.
        This is shared funciton for both formats (xml & tsv) that holdings
        come in.
        '''
        date = None
        if f008:
            y = int(f008[26:28])
            m = int(f008[28:30])
            if y and m:
                # Possibly when we hit 2080, if we are still using
                # this approach, then it maybe buggy -- 1980 or 2080.
                if y <= int(datetime.strftime(datetime.today(), '%y')):
                    y = 2000 + y
                else:
                    y = 1900 + y
                date = "%02i/%i" % (m, y)
        return date

    def load_xml_holding(self, record):
        # get the oclc number to link to
        oclc = _normal_oclc(_extract(record, '004'))
        if not oclc:
            _logger.error("holding record missing title: record %s, oclc %s" %
                         (self.records_processed, oclc))
            self.errors += 1
            return

        titles = self._get_related_title(oclc)
        if not titles:
            return

        # get the institution to link to
        inst_code = _extract(record, '852', 'a')
        inst = self._get_related_inst_code(inst_code)
        if not inst:
            return

        # get the holdings type
        holding_type = self._extract_holdings_type(record)

        # get the description
        desc = _extract(record, '866', 'a') or _extract(record, '866', 'z')
        notes = _extract(record, '852', 'z')

        # get the last modified date
        f008 = _extract(record, '008')
        date = self._parse_date(f008)

        # persist it
        for title in titles:
            holding = models.Holding(title=title,
                                     institution=inst,
                                     description=desc,
                                     type=holding_type,
                                     last_updated=date,
                                     notes=notes)
            holding.save()
            self.holding_created += 1
        reset_queries()

    def main(self, holdings_source):

        # first we delete any existing holdings
        holdings = models.Holding.objects.all()
        [h.delete() for h in holdings]

        # a holdings source can be one file or a directory of files.
        loader = HoldingLoader()
        _logger.info("loading holdings from: %s" % holdings_source)

        # check if arg passed is a file or a directory of files
        if os.path.isdir(holdings_source):
            holdings_dir = os.listdir(holdings_source)
            for filename in holdings_dir:
                holdings_file_path = os.path.join(holdings_source, filename)
                loader.load_file(holdings_file_path)
                loader.files_processed += 1
        else:
            loader.load_file(holdings_source)
            loader.files_processed += 1

        _logger.info("records processed: %i" % loader.records_processed)
        _logger.info("missing title: %i" % loader.missing_title)
        _logger.info("skipped: %i" % loader.skipped)
        _logger.info("errors: %i" % loader.errors)
        _logger.info("holdings saved: %i" % loader.holding_created)
        _logger.info("files processed: %i" % loader.files_processed)


def _holdings_type(s):
    if s[0] == "t":
        return "Original"
    elif s[0] == "h" and len(s) > 11:
        if s[11] == "a":
            return "Microfilm Master"
        elif s[11] == "b":
            return "Microfilm Print Master"
        elif s[11] == "c":
            return "Microfilm Service Copy"
        #other values are classified as generic microform
        #m - Mixed generation
        #u - Unknown
        #| - No attempt to code
        elif s[11] in ["m", "u", "|"]:
            return "Microform"
        else:
            return None
    elif s[0] == "c":
        return "Online Resource"
    elif s[0] == "z":
        return "Unspecified"
    else:
        return None
