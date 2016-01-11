import datetime
import logging
import os

from django.conf import settings
from django.utils.unittest import skipUnless
from django.test import TestCase
from worldcat.util.extract import extract_elements

from openoni.core.title_pull import (
    raw_query, str_value, TitlePuller,
)

__all__ = ['TitlePullTests']

_logging = logging.getLogger(__name__)


def _chk_if_test_dir_exists(test_dir=None):
    """
    Set test directory.
    If it exists & there is stuff in it, stop & set up test skipping.
    This test does not assume that it is safe to clear things out.

    If it doesn't exist, create it.
    If the creation fails, it is logged & tests that require it fail.
    """

    # Todo Move this to settings
    dir_to_chk = settings.TEMP_TEST_DATA
    skip_warn = "Skipping tests dependent on test_dir."
    if os.path.exists(dir_to_chk):
        if len(os.listdir(dir_to_chk)):
            _logging.warning("test_dir already exists & is not empty.")
            _logging.warning(skip_warn)
        else:
            # Directory exists, but it is empty, so we will use it
            test_dir = dir_to_chk
    else:
        try:
            os.makedirs(dir_to_chk)
            test_dir = dir_to_chk
        except OSError, e:
            warn = "Unable to create testing directory"
            _logging.warning("%s %s." % (warn, dir_to_chk))
            _logging.warning(skip_warn)
    return test_dir

def _clear_test_dir(test_dir=None):
    """
    Function to clear the test data directory.
    """
    cleared = False
    if test_dir:
        for f in os.listdir(test_dir):
            os.remove(os.path.join(test_dir, f))
            cleared = True
    else:
        _logging.warning("Tried to delete files in test_dir, but something happened.")
    return cleared

class TitlePullTests(TestCase):

    test_dir = _chk_if_test_dir_exists()

    @classmethod
    def setUpClass(cls):
        cls.t = TitlePuller()
        cls.srw = '{http://www.loc.gov/zing/srw/}'
        cls.test_case_rec = cls.t.generate_requests(oclc='18475650')
        cls.test_case_recs_range = cls.t.generate_requests(start=1979,
            end=1980, countries=['united states','puerto rico'])
        cls.test_case_recs_fake_cntry = cls.t.generate_requests(
            countries=['not a real country',])

    @classmethod
    def tearDownClass(cls):
        _logging.info("Removing test-pull dir & files.")
        cleared = _clear_test_dir(cls.test_dir)
        if cleared:
            os.rmdir(cls.test_dir)

    def test_str_value(self):
        test_value = str_value(42)
        self.assertEqual('0042', test_value)
        self.assertIsInstance(test_value, str)

    def test_generate_year_dict(self):

        # test output with out start & end dates passed
        yr_dict = self.t.generate_year_dict()
        len_special_cases = 2  # 0000 & 1000

        # is the output the right length?
        len_range_cases = datetime.datetime.now().year + 1 - 1800
        total = len_special_cases + len_range_cases
        self.assertEqual(total, len(yr_dict))

        # test output with start & end values passed
        yr_dict_with_dates = self.t.generate_year_dict(1776, 1976)
        self.assertEqual(201, len(yr_dict_with_dates))

        # these should be the same with or without dates
        # so, we are not going to test yr_dict_with_dates
        self.assertEqual('=', yr_dict['1000'])
        self.assertEqual('=', yr_dict['0000'])
        # validate operation sign for last item
        sorted_keys = sorted(yr_dict.keys())
        self.assertEqual('>=', yr_dict[sorted_keys[-1]])
        # validate operation that is lowest number that is not 1000 or 0000
        self.assertEqual('<=', yr_dict[sorted_keys[2]])

    def test_add_to_query(self):
        # Test without query string
        funct_out = self.t.add_to_query('srw.la', 'spa', 'exact')
        self.assertEqual(funct_out, 'srw.la exact "spa"')

        # Test with query string
        query = 'srw.pc any "y" and srw.mt any "newspaper"'
        results = self.t.add_to_query('srw.la', 'spa', 'exact', query)
        expected = 'srw.pc any "y" and srw.mt any "newspaper" and srw.la exact "spa"'
        self.assertEqual(results, expected)

    def test_generate_requests(self):

        # testing values of one country in
        cntries = ('guam',)
        guam_results = self.t.generate_requests(
            lccn=None, oclc=None, raw_query=raw_query,
            countries=cntries, totals_only=False
        )[0][2]
        expected = ('guam', 'all-yrs', '=')
        self.assertTupleEqual(guam_results, expected)

        # 2 countries in, 2 out
        cntries = ('guam', 'virgin island*')
        results = self.t.generate_requests(
            lccn=None, oclc=None, raw_query=raw_query,
            countries=cntries, totals_only=False
        )
        self.assertEqual(len(results), 2)

        # test a bad lccn pull
        results = self.t.generate_requests(lccn='sn-96095007')
        self.assertEqual(results[0][1], '0')
        # test a good lccn pull
        results = self.t.generate_requests(lccn='sn 96095007')
        self.assertEqual(results[0][1], '1')

        # testing what is actually returned from good lccn pull
        r_xml = results[0][0].response

        r_query = extract_elements(r_xml, element=self.srw + 'query')
        self.assertEqual(r_query[0].text, 'srw.dn exact "sn 96095007"')

        r_numofrecs = extract_elements(r_xml, element=self.srw + 'numberOfRecords')
        self.assertEqual(r_numofrecs[0].text, '1')

        r_schema = extract_elements(r_xml, element=self.srw + 'recordSchema')
        self.assertEqual(r_schema[0].text, 'info:srw/schema/1/marcxml')

        # testing requests split by years
        results = self.test_case_recs_range
        self.assertEqual(len(results), 4)

        # Confirm that everything that was returned is '='
        operator = list(set([r[2][2] for r in results]))
        self.assertEqual('=', operator[0])

        # testing oclc pull & the results
        r_xml = self.test_case_rec[0][0].response
        r_query = extract_elements(r_xml, element=self.srw + 'query')
        self.assertEqual(r_query[0].text, 'srw.no exact "18475650"')

        r_numofrecs = extract_elements(r_xml, element=self.srw + 'numberOfRecords')
        self.assertEqual(r_numofrecs[0].text, '1')

        # test something that is not a real country
        results = self.test_case_recs_fake_cntry
        self.assertFalse(bool(results))

    @skipUnless(test_dir,
        "Skipping test_grab_content, because problem with test directory.")
    def test_run(self):
        results = self.t.grab_content(self.test_dir, [])
        self.assertIsNone(results)

        _clear_test_dir(self.test_dir)
        files_saved = self.t.run(self.test_dir, start=1978, end=1979, countries=('puerto rico',))
        self.assertEqual(len(os.listdir(self.test_dir)), files_saved)
