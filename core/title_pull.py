import datetime
import itertools
import logging
import os
import requests
import StringIO
import sys
import time
import types
import urllib

from django.conf import settings

from worldcat.request.search import SRURequest
from worldcat.util.extract import extract_elements, pymarc_extract

WSKEY = settings.WORLDCAT_KEY
sortkeys = 'Date,,0'
recordschema = 'info:srw/schema/1/marcxml'
recordpacking = 'xml'
servicelevel = 'full'
frbrgrouping = 'off'
MAX_RECORDS = 50
raw_query = 'srw.pc any "y" and srw.mt any "newspaper"'  # and srw.cp exact "united states"

COUNTRIES = (
    'united states',
    'puerto rico',
    '*virgin island*',
    '*guam*',
    '*northern mariana*',
    'american samoa',
)

# operate map is used in passing the operator to the output file.
OPERATOR_MAP = {
    '=': 'e',
    '<=': 'lte',
    '>=': 'gte',
    '>': 'gt',
    '<': 'lt',
}


class SearchWorldCatTitles:

    # TODO: add class description

    year_breaks = []

    def __iter__(self):
        return self

    def generate_year_list(self, start=None, end=None):
        '''
        Generate a list of years to break up the query. OCLC API queries
        between 1000 and 2030 if not defined. Since we break up our requests
        by year, we are starting with 1800 as default and using the current
        year as the end.

        The final requests will pull records before 1800, but will be package
        them with 1800, because we will grab < 1800.

        Finally, there is a list of special cases to query against. This
        is to handle unknown dates such as 'uuuu' and '1uuu'.
        '''

        if not start:
            start = 1800

        if not end:
            now = datetime.datetime.now()
            end = now.year

        # Numbers are converted to strings, because we want 0000, not 0.
        special_yr_cases = ['0000', '1000']

        year_and_action = {}
        year_and_action[str(start)] = '<='

        for year in (range(start + 1, end) + special_yr_cases):
            year_and_action[str(year)] = '='

        year_and_action[str(end)] = '>='
        return year_and_action

    def add_to_query(self, query, oclc_field, value, relationship):
        '''
        Add to the query more values.
        For example, this:
        self.add_to_query(query, 'srw.cp', 'united states', 'exact')
        Will add this to the query you pass:
        'and srw.cp exact "united states"'
        '''

        field_query = ' and %s %s "%s"' % (oclc_field, relationship, value)
        new_query = query + field_query
        return new_query

    def generate_srurequest(self, query):
        bib_rec = SRURequest(wskey=WSKEY,
                             sortKeys=sortkeys,
                             recordSchema=recordschema,
                             recordPacking=recordpacking,
                             servicelevel=servicelevel,
                             query=query,
                             startRecord=1,
                             maximumRecords=MAX_RECORDS,
                             frbrGrouping=frbrgrouping)

        return bib_rec

    def generate_requests(self, query=raw_query, countries=COUNTRIES,
                          totals_only=False):
        '''
        TODO: add a description
        '''

        # create an empty list of bib_recs_to_execute.
        bibs_to_req = []
        grand_total = 0

        for country in countries:
            total = 0
            cntry_query = self.add_to_query(query, 'srw.cp', country, 'exact')

            # Add this point we have something like this for the cntry_query
            # srw.pc any "y" and srw.mt any "newspaper" and srw.cp exact "united states"

            cntry_req = self.generate_srurequest(cntry_query)
            cntry_count = self.initial_total_count(cntry_req)
            request_able = self.check_for_doable_request(cntry_count)

            logging.info("%s request totals: %s" % (country.title(),
                                                    cntry_count))

            if request_able:
                # If we can pull the whole country at once, we will
                # otherwise we break it up into multiple requests.
                bibs_to_req.append((cntry_req,
                                    request_able,
                                    country.strip('*'),
                                    'all-yrs',
                                    '='))
            else:
                # generate split requests by year
                # so the responses are small enough for the OCLC API to handle
                year_list = self.generate_year_list()
                total = 0
                for year in year_list:

                    operator = year_list[year]

                    year_query = self.add_to_query(cntry_query, 'srw.yr',
                                                   year, operator)
                    #self.generate_year_query(year, cntry_query, operator)
                    yr_request = self.generate_srurequest(year_query)

                    yr_count = self.initial_total_count(yr_request)
                    yr_request_able = self.check_for_doable_request(yr_count)

                    logging.info("%s, %s %s total: %s" % (country.title(),
                                                          operator, year,
                                                          yr_request_able))
                    if yr_request_able:
                        bibs_to_req.append((yr_request, yr_request_able,
                                            country.strip('*'),
                                            year, operator))
                    else:
                        logging.warning("The request is too large. Break down \
                                        further.")
                        return

                    total += yr_request_able
            grand_total += total

        logging.info('GRAND TOTAL: %s' % (grand_total))

        return bibs_to_req

    def grab_content(self, data_save_path, bib_requests,
                     search_name='ndnp'):
        '''
        TODO: Write a new description. :-(

        '''
        # Run each request and save content.
        for bib_rec in bib_requests:
            grab_records = True
            counter = 0
            bib_request, total, cntry, divider, operator = bib_rec

            while grab_records:
                bib_resp = next_record = next = end = start = None
                counter += 1

                # grab xml
                bib_resp = bib_request.get_response()
                # identify the xml field of next record number from the xml
                next_record = extract_elements(bib_request.response,
                                               element='{http://www.loc.gov/zing/srw/}nextRecordPosition')

                # grab the text from next_record to get the actual value
                try:
                    next = next_record[0].text
                except IndexError:
                    # no more recs to grab
                    grab_records = False

                try:
                    end = int(next) - 1
                except TypeError:
                    end = total

                try:
                    start = int(next) - MAX_RECORDS
                except TypeError:
                    if counter == 1:
                        start = 1
                    else:
                        start = previous_next

                # print cntry, total, start, end, next, divider, operator
                if start is None:
                    # Stop grabbing records
                    grab_records = False

                if counter == 1:
                    logging.info('Batch: %s %s for %s = %s total' %
                                 (operator, divider, cntry, total))

                # Create directory if it doesn't exist
                if not os.path.exists(data_save_path):
                    os.makedirs(data_save_path)

                filename = '%s_%s_%s_%s_%s_to_%s.xml' % (search_name,
                                                      cntry.replace(' ', '-'),
                                                      divider,
                                                      OPERATOR_MAP[operator],
                                                      str(start), str(end))

                file_location = data_save_path + filename

                save_file = open(file_location, "w")
                decoded_data = bib_resp.data.decode("utf-8")
                save_file.write(decoded_data.encode('ascii', 'xmlcharrefreplace'))
                save_file.close()

                try:
                    previous_next = next
                    bib_request.next()
                except StopIteration:
                    # Break loop and continue on to next year combination
                    grab_records = False

        return

    def initial_total_count(self, bib_req):
        '''
        This function hits request three times and returns list of totals from
        each hit. This is used to access the quality of results returned.
        '''
        totals = []

        for grab in itertools.repeat(None, 3):
            bib_req.get_response()
            _total = extract_elements(bib_req.response,
                                      element='{http://www.loc.gov/zing/srw/}numberOfRecords')
            totals.append(_total[0].text)

            #TODO: Check for request time w/ each request
            # If the request takes more than 10 seconds,
            # Kill function & split request. Chk split requests.
        return totals

    def check_for_doable_request(self, test_totals):

        # If all 3 pulls are the same
        if all(map(lambda x: x == test_totals[0], test_totals)):
            # if all are the same, check that the request is managable.
            if int(test_totals[0]) < 10000:
                return int(test_totals[0])
            else:
                return None
        else:
            # If this test_totals do not match, the query broke API
            # Split needs to occur
            return None

    def run(self, data_save_path, query=None):
        '''
        Function that runs a search against the WorldCat Search API

        The default query is:
        for country in COUNTRIES:
            'srw.pc any "y" and srw.mt any "newspaper"' + country

        If you pass a string as the query, then it will over ride
        and pull for that query.
        Response is stored in data if no argument is passed.
        '''

        if query:
            # Make sure the query is a string
            try:
                # make sure the query passed is a string
                assert isinstance(query, types.StringType)
                self.grab_content(query, data_save_path)
            except AssertionError:
                query_type = type(query)
                # TODO: Turn into warning log error
                print "Please provide a list or leave blank for \
                        default handling. You provided a %s." % (query_type)
        else:
            # Default runs query at the top of the file.

            bib_requests = self.generate_requests()
            self.grab_content(data_save_path, bib_requests)


def main(data_save_path='data/'):
    logging.basicConfig(filename='worldcat_search.log', level=logging.INFO)
    logging.info('Starting World Cat title search.')

    search = SearchWorldCatTitles()

    search.run(data_save_path)
    logging.info('Finished World Cat title search.')


if __name__ == '__main__':
    main()
