import csv
import logging
import os
import re
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
        self.count = 0
        self.errors = 0
        self.skipped = 0

        self.desc_error = 0
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

        def load_csv_file(file_name):
            '''
            Load csv file was created to handle csv holdings.
            The update file acquired in 2010 was in csv format.
            However, the new holdings file was in xml format.
            This code is being left in this file until we have a
            discussion about future possibilities of formats.

            Instead of map_xml, you would call load_csv_file.
            Shared functioned between load_xml & load_csv were
            pulled out.
            '''
            self.files_processed += 1
            for row in csv.DictReader(open(file_name),
                                        delimiter='\t',
                                        quotechar='\x07',
                                        lineterminator='\n',
                                        quoting=csv.QUOTE_NONE):

                self.records_processed += 1
                # We only want to pull out records that are newspapers,
                # hence 'n'.
                srtp = row['SrTp']
                if srtp.strip().lower() == 'n':
                    try:
                        self.load_csv_holding(row)
                    except Exception, e:
                        _logger.error("unable to load record %s: %s" %
                                    (self.records_processed, e))
                        _logger.exception(e)
                        self.errors += 1
                else:
                    self.skipped += 1

        map_xml(load_xml_record, file(filename, "rb"))

    def _get_related_title(self, oclc):
        '''
        Match the title via oclc number or record an error.
        '''
        try:
            title = models.Title.objects.get(oclc=oclc)
            return title
        except models.Title.DoesNotExist:
            _logger.error("Holding missing Title to link: record %s, oclc %s" %
                            (self.records_processed, oclc))
            self.missing_title += 1
            self.errors += 1
            return None

    def _get_related_inst_code(self, inst_code):
        '''
        Match the institutional code or record an error.
        '''
        try:
            inst = models.Institution.objects.get(code=inst_code)
            return inst
        except models.Institution.DoesNotExist:
            _logger.error("Holding missing Institution to link to: %s" %
                          inst_code)
            self.errors += 1
            return None

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
            # TODO: should this handle 2 digit years better?
            if y and m:
                if y < 10:
                    y = 2000 + y
                else:
                    y = 1900 + y
                date = "%02i/%i" % (m, y)
        return date

    def load_csv_holding(self, record):
        '''
        This function parses and loads a single line from a csv
        holdings file. This was written to work with holdings that
        were acquired in 2010, however new data needed to be
        acquired for better accuracy. As a result, it was never
        used in production. However, it maybe be of use to someone the
        next time we load holdings.

        The holdings that this function was based off of are located here:
        http://sun9.loc.gov:8088/transfer/inventory/bag/2462

        Please note: There are  pending issues with the dataset,
        which maybe reflected in the function below. One of the pending
        issues was that the holdings were summary holdings. Another issue
        with the dataset was that the db requires 866 field, but not all
        rows had that field. Some had alternate fields, which are noted
        in the code below.
        '''

        def _search_marc_str(search_str, subfield_str):
            '''
            This function parses out the value that is located between the
            subfield_str & the following '$'.

            For example...
            search_str = '852 8  $a LUU$b LUUE$c STACKS$h MICROPRINT 15'
            subfield_str = 'a'
            returned value is 'LUU'
            '''
            try:
                # If the value exists, then we look for value in between the
                # search string & the next '$'.
                subfield_search = '\$' + subfield_str + ' (.*?)\$'
                value = re.compile(subfield_search).search(search_str)

                if not value:
                    # If the value isn't followed by a '$', then it is the last
                    # value of the string, so we take everything to the end of
                    # the string
                    subfield_search_end = '\$' + subfield_str + ' (.*?)$'
                    value = re.compile(subfield_search_end).search(search_str)

                return value.group(1)

            except AttributeError:
                return None

        oclc = record['OCLC No.']
        if not oclc:
            _logger.error("holding record missing title: record %s, oclc %s" %
                            (self.records_processed, oclc))
            self.no_oclc += 1
            self.errors += 1
            return

        title = self._get_related_title(oclc)
        if not title:
            return

        LHR_852 = record['LHR 852']

        # get the institution to link to
        inst_code = _search_marc_str(LHR_852, 'a')
        inst = self._get_related_inst_code(inst_code)
        if not inst:
            self.miss_inst_codes.append(inst_code)
            return

        # get the holdings type
        holding_type = _search_marc_str(LHR_852, 't')

        # grab all extra fields to look for 866/desc field
        LHR_misc = []
        # the header labeled LHR Misc Fields could contain an 866 value
        LHR_misc.append(record['LHR Miscellaneous Fields'])
        try:
            # or any value with no header could contain an 866 value
            [LHR_misc.append(x) for x in record[None]]
        except KeyError:
            self.desc_error += 1
            _logger.error("missing LHR_misc field: record %s, oclc %s" %
                            (self.records_processed, oclc))
            return

        # check if misc field is a desc (866) or not.
        # other values seen in this field are 853, 863 & 876
        f866 = desc = None
        if LHR_misc:
            f866 = [v for v in LHR_misc if v.startswith('866')]
            f863 = [v for v in LHR_misc if v.startswith('863')]

        if f866:
            # possible values for 866 are not stored in separate fields,
            # so we need to concatinate the string to match other records
            if f863:
                _logger.error("missing LHR_misc field: record %s, oclc %s" %
                            (self.records_processed, oclc))
                return

            f866_vals = []
            for f866_item in f866:
                f866_val = (_search_marc_str(f866_item, 'a') or
                            _search_marc_str(f866_item, 'z'))
                f866_vals.append(f866_val)
            desc = ', '.join(f866_vals)

        if not desc:
            self.desc_error += 1
            _logger.error("missing description: record %s, oclc %s" %
                            (self.records_processed, oclc))
            return

        # get the last modified date
        f008 = record['LHR 008 - Complete Field']
        date = self._parse_date(f008)

        # persist it
        holding = models.Holding(title=title,
                                 institution=inst,
                                 description=desc,
                                 type=holding_type,
                                 last_updated=date)

        holding.save()
        self.holding_created += 1
        reset_queries()

    def load_xml_holding(self, record):
        # get the oclc number to link to
        oclc = _normal_oclc(_extract(record, '004'))
        if not oclc:
            _logger.error("holding record missing title: record %s, oclc %s" %
                         (self.records_processed, oclc))
            self.errors += 1
            return

        title = self._get_related_title(oclc)
        if not title:
            return

        # get the institution to link to
        inst_code = _extract(record, '852', 'a')
        inst = self._get_related_inst_code(inst_code)
        if not inst:
            return

        # get the holdings type
        holding_type = _holdings_type(_extract(record,'007'))

        # get the description
        desc = _extract(record, '866', 'a') or _extract(record, '866', 'z')
        if not desc:
            _logger.error("missing description: record %s, oclc %s" %
                         (self.records_processed, oclc))
            return

        # get the last modified date
        f008 = _extract(record, '008')
        date = self._parse_date(f008)

        # persist it
        holding = models.Holding(title=title,
                                 institution=inst,
                                 description=desc,
                                 type=holding_type,
                                 last_updated=date)
        holding.save()
        reset_queries()

    def main(self, holdings_source):

        # first we delete any existing holdings
        # TODO: Add some transaction management
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
        else:
            loader.load_file(holdings_source)

        _logger.info("records processed: %i" % loader.records_processed)
        _logger.info("missing title: %i" % loader.missing_title)
        _logger.info("skipped: %i" % loader.skipped)
        _logger.info("errors: %i" % loader.errors)
        _logger.info("Record count: %i" % loader.count)
        _logger.info("Desc issues: %i" % loader.desc_error)
        _logger.info("Holdings saved: %i" % loader.holding_created)
        _logger.info("No oclc number: %i" % loader.no_oclc)
        #_logger.info("Strp = 'n': %i" % loader.n)
        _logger.info("Files processed: %i" % loader.files_processed)


def _holdings_type(s):
    if s[0] == "t":
        return "Original"
    elif s[0]  == "h" and s[11] == "a":
        return "Microfilm Master"
    elif s[0] == "c":
        return "Electronic Resource"
    elif s[0] == "z":
        return "Unspecified"
    else:
        return None
