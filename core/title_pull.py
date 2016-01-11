import datetime
import itertools
import logging
import os
import sys

from django.conf import settings

from worldcat.request.search import SRURequest
from worldcat.util.extract import extract_elements

_logger = logging.getLogger(__name__)

WSKEY = settings.WORLDCAT_KEY
sortkeys = 'Date,,0'
recordschema = 'info:srw/schema/1/marcxml'
recordpacking = 'xml'
servicelevel = 'full'
frbrgrouping = 'off'
MAX_RECORDS = 50
raw_query = 'srw.pc any "y" and srw.mt any "newspaper"'  # and srw.cp exact "united states"

# Texas should not be a country.
# See ticket #1226 for the reason why it is in this list.
COUNTRIES = (
    'united states',
    'puerto rico',
    'virgin island*',
    'guam',
    '*northern mariana*',
    'american samoa',
    'texas',
)

# operate map is used in passing the operator to the output file.
OPERATOR_MAP = {
    '=': 'e',
    '<=': 'lte',
    '>=': 'gte',
    '>': 'gt',
    '<': 'lt',
}


def str_value(value):
    '''
    Turn the value into at least a 4 digit string.
    This is used in the naming of files.
    '''
    str_value = str(value)
    while len(str_value) < 4:
        str_value = '0' + str_value
    return str_value


class TitlePuller(object):

    """
    Title puller class pulls files from OCLC's Worldcat API,
    based on params passed.

    Best place to start is with the run method. Run defaults to
    a generic pull for openoni, unless a query is passed.
    """


    year_breaks = []

    def generate_year_dict(self, start=None, end=None):
        '''
        Generate a list of years to break up the query. OCLC API queries
        between 1000 and 2030 if not defined. Our main use case is after 1800.
        Since we break up our requests by year, we are starting
        with 1800 as default and using the current year as the end.

        The final requests will pull records before 1800, but will be package
        them with 1800, because we will grab < 1800.

        OCLC indexes unknown values with zeros. So, uuuu will be indexed
        as 0000 & 1uuu will be indexed as 1000. For that reason,
        we explicitly add 0000 & 1000 to the list of years to query.

        Finally, this function will except a start & an end value. If
        a start or end value is passed then the special cases 0000 & 1000
        are ignored. This is so the user has control & extra records are
        not added. It should be noted that a date such as 19uu will be
        indexed as 1900 & 195u will be indexed as 1950.
        '''

        year_and_action = {}

        # We only include 0000 & 1000 if there is no explicit start & end.
        # We do check this first, b/c we are going to make adjustments
        # to start & end values.
        if not start or not end:
            # Numbers are converted to strings, because we want 0000, not 0.
            special_yr_cases = ['0000', '1000']
        else:
            special_yr_cases = []

        if start:
            year_and_action[str(start)] = '='
        else:
            start = 1800
            year_and_action[str(start)] = '<='

        if end:
            year_and_action[str(end)] = '='
        else:
            now = datetime.datetime.now()
            end = now.year
            year_and_action[str(end)] = '>='

        for year in (range(start + 1, end) + special_yr_cases):
            year_and_action[str(year)] = '='

        # example if start & end are passed:
        # {'1949': '=', '1951': '=', '1950': '=', '1952': '='}
        # example if no start & end:
        # {'0000': '=', '1000': '=', '1800': '<=', '1801': '=',
        # '1802': '=', ... '2012': '=', '2013': '>='}
        return year_and_action

    def add_to_query(self, oclc_field, value, relationship, query=None):
        '''
        Add additional values to the base query
        For example, this:
        self.add_to_query(query, 'srw.la', 'spa', 'exact')

        Will add this to the query you pass:
        'srw.la exact "spa"'
        and if there is a query value, then...
        query + 'and srw.la exact "spa"'

        More info on indexes to query:
        http://oclc.org/developer/documentation/worldcat-search-api/complete-list-indexes
        '''
        new_query = '%s %s "%s"' % (oclc_field, relationship, value)
        if query:
            new_query = '%s and %s' % (query, new_query)
        return new_query

    def generate_srurequest(self, query):
        '''
        Generates the SRURequest used to query OCLC API.
        Most of the values are static, except for query.
        '''
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

    def generate_requests(self, lccn=None, oclc=None, raw_query=raw_query, countries=COUNTRIES,
                          start=None, end=None, totals_only=False):
        '''
        Generate request(s) is a function that generates a set of requests
        to be executed against the OCLC API. A set of requests can be
        just one request, example an lccn, or it can be a larger title pull.
        '''
        # create an empty list of bib_recs_to_execute.
        bibs_to_req = []
        # if this request is lccn or oclc specific, create 1 request
        # otherwise, create them for all the 'countries' in the country list
        if lccn or oclc:

            if lccn:
                query = self.add_to_query('srw.dn', lccn, 'exact')
            elif oclc:
                query = self.add_to_query('srw.no', oclc, 'exact')

            request = self.generate_srurequest(query)
            lccn_count = self.initial_total_count(request)
            bibs_to_req.append((request, lccn_count[0], (lccn,)))

        else:
            grand_total = 0
            for country in countries:
                total = 0
                query = self.add_to_query('srw.cp', country, 'exact', raw_query)

                # We want to force this to pass through the year dividing
                # pass below.
                if start or end:
                    request_able = None
                else:
                    # Add this point we have something like this for the cntry_query
                    # srw.pc any "y" and srw.mt any "newspaper" and
                    # srw.cp exact "puerto rico"
                    cntry_req = self.generate_srurequest(query)
                    cntry_count = self.initial_total_count(cntry_req)
                    request_able = self.check_for_doable_bulk_request(cntry_count)

                    _logger.info("%s request totals: %s" % (country.title(),
                                                        cntry_count))

                if request_able == 0:
                    # There is no valid requests at all. So, we exit.
                    _logger.warning('No records returned for: %s' % (country))
                elif request_able:
                    # If we can pull the whole country at once, we will
                    # otherwise we break it up into multiple requests.
                    bibs_to_req.append((cntry_req, request_able, (
                                        country.strip('*'), 'all-yrs', '='
                                        )))
                    total += request_able
                else:
                    # generate split requests by year
                    # so the responses are small enough for the OCLC API to handle
                    year_dict = self.generate_year_dict(start=start, end=end)
                    base_query = query

                    for year in sorted(year_dict.iterkeys()):
                        operator = year_dict[year]
                        query = self.add_to_query('srw.yr', year, operator, base_query)
                        yr_request = self.generate_srurequest(query)
                        yr_count = self.initial_total_count(yr_request)
                        yr_request_able = self.check_for_doable_bulk_request(yr_count)

                        _logger.info("%s - %s %s total: %s" % (
                            country.title(), year, operator, yr_request_able))

                        if yr_request_able or year == str(datetime.datetime.now().year):
                            bibs_to_req.append((yr_request, yr_request_able, (
                                                country.strip('*'), year, operator
                                                )))
                        else:
                            _logger.warning("There is a problem with request. Exiting.")
                            _logger.warning('yr_request: %s' % yr_request)
                            _logger.warning('yr_request_able: %s' % yr_request_able)
                            _logger.warning('country: %s' % country.strip('*'))
                            _logger.warning('year: %s' % year)
                            _logger.warning('operator: %s' % operator)

                            continue

                        total += yr_request_able
                grand_total += total
            _logger.info('GRAND TOTAL: %s' % (grand_total))

        return bibs_to_req

    def grab_content(self, save_path, bib_requests, search_name='ndnp'):
        '''
        Loops over all requests, executes request & saves response
        to the designated 'save_path'.
        '''
        # Run each request and save content.
        if not bib_requests:
            return

        files_saved = 0
        for bib_rec in bib_requests:
            grab_records = True
            counter = 0
            bib_request, total, components = bib_rec
            previous_next = None

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

                if start is None:
                    grab_records = False

                name_components = []
                for i in components:
                    i = i.replace(' ', '-')
                    if i in OPERATOR_MAP:
                        i = OPERATOR_MAP[i]
                    name_components.append(i)

                batch_name = '_'.join(name_components)

                filename = '_'.join((search_name, batch_name, str_value(start), str_value(end))) + '.xml'

                if counter == 1 and len(bib_requests) > 1:
                    _logger.info('Batch: %s = %s total' % (filename, total))

                file_location = save_path + '/' + filename

                save_file = open(file_location, "w")
                decoded_data = bib_resp.data.decode("utf-8")
                save_file.write(decoded_data.encode('ascii', 'xmlcharrefreplace'))
                save_file.close()
                files_saved += 1

                try:
                    previous_next = next
                    bib_request.next()
                except StopIteration:
                    # Break loop and continue on to next year combination
                    grab_records = False

        return files_saved

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
        return totals

    def check_for_doable_bulk_request(self, test_totals):
        '''
        This function compares the results returned from the 3 requests
        passed in test_totals. The API could misfire when requesting
        more than 10k, so we make sure that are requests aren't that large.
        '''
        # If all 3 pulls are the same
        if all(map(lambda x: x == test_totals[0], test_totals)):
            # if all are the same, check that the request is managable.
            # requests over 10000 records will cause failure on the OCLC side
            if int(test_totals[0]) < 10000:
                return int(test_totals[0])
        # if this test_totals do not match, the query broke API
        # or the total is over 10000
        # split needs to occur
        return None

    def run(self, save_path, lccn=None, oclc=None,
        start=None, end=None, countries=COUNTRIES):
        '''
        Function that runs a search against the WorldCat Search API

        The default query is:
        for country in COUNTRIES:
            'srw.pc any "y" and srw.mt any "newspaper"' + country

        If you pass a string as the query, then it will over ride
        and pull for that query.
        Response is stored in data if no argument is passed.
        '''
        # Create directory if it doesn't exist
        if not os.path.exists(save_path):
            try:
                os.makedirs(save_path)
            except OSError:
                _logger.exception('Issue creating the directory %s.' % save_path)
                sys.exit()
        else:
            # Make sure the directory is empty
            if len([f for f in os.listdir(save_path) if os.path.isfile(f)]):
                _logger.exception('Destination directory %s is not empty.' % save_path)
                sys.exit()

        files_saved = 0
        # Default runs query at the top of the file.
        # If lccn, then it pulls only that lccn, otherwise it will do
        # a bulk download of titles.
        bib_requests = self.generate_requests(lccn=lccn, oclc=oclc,
            start=start, end=end, countries=countries)
        files_saved = self.grab_content(save_path, bib_requests)

        return files_saved
