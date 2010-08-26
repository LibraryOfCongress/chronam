import re
import logging
from urllib import urlencode

from solr import SolrConnection
from django.core.paginator import Paginator, Page
from django.db import connection, reset_queries
from django.http import QueryDict
from django.conf import settings

from chronam.core import models
from chronam.core.title_loader import _normal_lccn
from chronam import utils

_log = logging.getLogger(__name__)

PROX_DISTANCE_DEFAULT = 5

# TODO: prefix functions that are intended for local use only with _

def page_count():
    solr = SolrConnection(settings.SOLR)
    return solr.query('type:page', fields=['id']).numFound

def title_count():
    solr = SolrConnection(settings.SOLR)
    return solr.query('type:title', fields=['id']).numFound

# TODO: use solr.SolrPaginator and update or remove SolrPaginator

class SolrPaginator(Paginator):
    """
    SolrPaginator takes a QueryDict object, builds and executes a solr query for
    newspaper pages, and returns a paginator for the search results for use in 
    a HTML form.
    """

    def __init__(self, query):
        self.query = query.copy()

        # figure out the solr query and execute it
        solr = SolrConnection(settings.SOLR) # TODO: maybe keep connection around?
        q = page_search(self.query)
        try:
            page_num = int(self.query.get('page', 1))
        except ValueError, e:
            page_num = 1
        rows = int(self.query.get('rows', 10))
        start = page_num * rows - 10
        params = {"hl.snippets": 100, # TODO: make this unlimited
            "hl.requireFieldMatch": 'true', # limits highlighting slop
            } 
        sort_field, sort_order = _get_sort(self.query.get('sort'), in_pages=True)
        solr_response = solr.query(q, 
                                   fields=['id', 'title', 'date', 'sequence',
                                           'edition_label', 'section_label'], 
                                   highlight=['ocr'],
                                   rows=rows,
                                   sort=sort_field,
                                   sort_order=sort_order,
                                   start=start,
                                   **params)

        pages = []
        for result in solr_response.results:
            page = models.Page.lookup(result['id'])
            if not page: 
                continue
            words = set()
            coords = solr_response.highlighting[result['id']]
            for s in coords.get('ocr') or []:
                words.update(find_words(s))
            page.words = "+".join(words)
            pages.append(page)

        # set up some bits that the Paginator expects to be able to use
        Paginator.__init__(self, pages, per_page=rows, orphans=0)
        self._count = int(solr_response.results.numFound)
        self._num_pages = None
        self._cur_page = page_num

    def page(self, number):
        """
        Override the page method in Paginator since Solr has already
        paginated stuff for us.
        """
        number = self.validate_number(number)
        return Page(self.object_list, number, self)

    def pages(self):
        """
        pages creates a list of two element tuples (page_num, url)
        rather than displaying all the pages for large result sets
        it provides windows into the results like digg:

           1 2 3 ... 8 9 10 11 12 13 14 ... 87 88 89

        """
        pages = []

        # build up the segments
        before = []
        middle = []
        end = []
        for p in self.page_range:
            if p <= 3:
                before.append(p)
            elif self._num_pages - p <= 3:
                end.append(p)
            elif abs(p - self._cur_page) < 5:
                middle.append(p)

        # create the list with '...' where the sequence breaks
        last = None 
        q = self.query.copy()
        for p in before + middle + end:
            if last and p - last > 1:
                pages.append(['...', None])
            else:
                q['page'] = p
                pages.append([p, urlencode(q)])
            last = p

        return pages

    def englishify(self):
        """
        Returns some pseudo english text describing the query. 
        """
        d = self.query
        parts = []
        if d.get('ortext', None):
            parts.append(' OR '.join(d['ortext'].split(' ')))
        if d.get('andtext', None):
            parts.append(' AND '.join(d['andtext'].split(' ')))
        if d.get('phrasetext', None):
            parts.append('the phrase "%s"' % d['phrasetext'])
        if d.get('proxtext', None):
            proxdistance = d.get('proxdistance', PROX_DISTANCE_DEFAULT)
            parts.append('%s within %s words proximity' % (d['proxtext'], 
                         proxdistance))
        return parts



    # TODO: see ticket #176
    # i think this can be removed if the search pages results view uses
    # css to orient pages, rather than fixing them in a table. other views
    # currently do the floating css so it should be easy to copy, and it 
    # would be nice to simplify this module.
    def results_table(self):
        """
        creates a two-dimensional array of results for easy
        display as a table in a django template
        """
        table = []
        objects = self.object_list
        for i in range(0, len(objects), 2):
            h = objects[i]
            row = [h]
            if i+1 < len(objects):
                h = objects[i+1]
                row.append(h)
            else:
                row.append(None)
            table.append(row)
        return table


# TODO: remove/update this in light of solr.SolrPaginator

class SolrTitlesPaginator(Paginator):
    """
    SolrTitlesPaginator takes a QueryDict object, builds and executes a solr 
    query for newspaper titles, and returns a paginator for the search results 
    for use in a HTML form.
    """

    def __init__(self, query):
        self.query = query.copy()

        # figure out the solr query
        q = title_search(self.query)

        try:
            page = int(self.query.get('page', 1))
        except ValueError:
            page = 1

        rows = int(self.query.get('rows', 50))
        start = page * rows - 50

        # determine sort order
        sort_field, sort_order = _get_sort(self.query.get('sort'))

        # execute query
        solr = SolrConnection(settings.SOLR) # TODO: maybe keep connection around?
        solr_response = solr.query(q, 
                                   fields=['lccn', 'title',
                                           'edition', 
                                           'place_of_publication', 
                                           'start_year', 'end_year',
                                           'language'], 
                                   rows=rows,
                                   sort=sort_field,
                                   sort_order=sort_order,
                                   start=start)

        # convert the solr documents to Title models
        # could use solr doc instead of going to db, if performance requires it
        lccns = [d['lccn'] for d in solr_response.results]
        results = []
        for lccn in lccns:
            try:
                title = models.Title.objects.get(lccn=lccn)
                results.append(title)
            except models.Title.DoesNotExist, e:
                pass # TODO: log exception 

        # set up some bits that the Paginator expects to be able to use
        Paginator.__init__(self, results, per_page=rows, orphans=0)
        self._count = int(solr_response.results.numFound) 
        self._num_pages = None
        self._cur_page = page

    def page(self, number):
        """
        Override the page method in Paginator since Solr has already
        paginated stuff for us.
        """
        number = self.validate_number(number)
        return Page(self.object_list, number, self)


def title_search(d):
    """
    Pass in form data for a given title search, and get back
    a corresponding solr query.
    """
    q = ["+type:title"]
    if d.get('state'):
        q.append('+state:"%s"' % d['state'])
    if d.get('county'):
        q.append('+county:"%s"' % d['county'])
    if d.get('city'):
        q.append('+city:"%s"' % d['city'])
    for term in d.get('terms', '').replace('"', '').split():
        q.append('+(title:"%s" OR essay:"%s" OR note:"%s" OR edition:"%s" OR place_of_publication:"%s" OR url:"%s")' % (term, term, term, term, term, term))
    if d.get('frequency'):
        q.append('+frequency:"%s"' % d['frequency'])
    if d.get('language'):
        q.append('+language:"%s"' % d['language'])
    if d.get('ethnicity'):
        q.append('+' + _expand_ethnicity(d['ethnicity']))
    if d.get('labor'):
        q.append('+subject:"%s"' % d['labor'])
    if d.get('year1') and d.get('year2'):
        # don't add the start_year restriction if it's the lowest allowed year
        if d.get('year1') != '1690':
            q.append('+end_year:[%s TO 9999]' % d['year1'])
        # don't add the end_year restriction if it's the max allowed year
        # particularly important for end_years that are coded as 'current'
        if d.get('year2') != '2009':
            q.append('+start_year: [0 TO %s]' % d['year2'])
    if d.get('lccn'):
        q.append('+lccn:"%s"' % _normal_lccn(d['lccn']))
    if d.get('materialType'):
        q.append('+holding_type:"%s"' % d['materialType'])
    q = ' '.join(q)
    return q


def page_search(d):
    """
    Pass in form data for a given page search, and get back
    a corresponding solr query.
    """
    q = ['+type:page']

    if d.get('lccn', None):
        q.append(query_join(d.getlist('lccn'), 'lccn'))

    if d.get('state', None):
        q.append(query_join(d.getlist('state'), 'state'))

    date_filter_type = d.get('dateFilterType', None)
    if date_filter_type == 'year' and d.get('year', None):
            q.append('+date:[%(year)s0101 TO %(year)s1231]' % d)
    elif date_filter_type == 'range' and d.get('date1', None) \
        and d.get('date2', None):
        d1 = _solrize_date(d['date1'])
        d2 = _solrize_date(d['date2'], is_start=False)
        if d1 and d2:
            q.append('+date:[%i TO %i]' % (d1, d2))

    if d.get('ortext', None):
        q.append(query_join(d['ortext'].split(' '), 'ocr'))

    if d.get('andtext', None):
        q.append(query_join(d['andtext'].split(' '), 'ocr', and_clause=True))

    if d.get('phrasetext', None):
        phrase = d['phrasetext'].replace('"', '')
        q.append('+ocr:"%s"' % phrase)

    if d.get('proxtext', None):
        distance = d.get('proxdistance', PROX_DISTANCE_DEFAULT)
        q.append('+ocr:"%s"~%s' % (d['proxtext'], distance))

    return ' '.join(q)


def query_join(values, field, and_clause=False):
    """
    helper to create a chunk of a lucene query, based on 
    some value(s) extracted from form data
    """

    # might be single value or a list of values
    if not isinstance(values, list):
        values = [values]

    # remove any quotes
    values = [v.replace('"', '') for v in values]

    # quote values
    values = ['"%s"' % v for v in values]

    # add + to the beginnging of each value if we are doing an AND clause 
    if and_clause:
        values = ["+%s" % v for v in values]

    # return the lucene query chunk
    return "+%s:(%s)" % (field, ' '.join(values))


def find_words(s):
    ems = re.findall('<em>.+?</em>', s)
    words = map(lambda em: em[4:-5], ems) # strip <em> and </em>
    return words


def index_titles(since=None):
    """index all the titles and holdings that are modeled in the database
    if you pass in a datetime object as the since parameter only title
    records that have been created since that time will be indexed.
    """
    cursor = connection.cursor()
    solr = SolrConnection(settings.SOLR)
    if since:
        cursor.execute("SELECT lccn FROM titles WHERE created >= '%s'" % since)
    else:
        solr.delete_query('type:title')
        cursor.execute("SELECT lccn FROM titles")

    count = 0
    while True:
        row = cursor.fetchone()
        if row == None: 
            break
        title = models.Title.objects.get(lccn=row[0])
        index_title(title, solr)
        count += 1
        if count % 100 == 0:
            _log.info("indexed %s titles" % count)
            reset_queries()
            solr.commit()
    solr.commit()

def index_title(title, solr=None):
    if solr==None:
        solr = SolrConnection(settings.SOLR)
    _log.info("indexing title: lccn=%s" % title.lccn)
    try:
        solr.add(**title.solr_doc)
    except Exception, e:
        _log.exception(e)        

def delete_title(title):
    solr = SolrConnection(settings.SOLR)
    q = '+type:title +id:%s' % title.solr_doc['id']
    r = solr.delete_query(q)
    _log.info("deleted title %s from the index" % title)

def index_pages():
    """index all the pages that are modeled in the database
    """
    _log = logging.getLogger(__name__)
    solr = SolrConnection(settings.SOLR)
    solr.delete_query('type:page')
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM pages")
    count = 0
    while True:
        row = cursor.fetchone()
        if row == None:
            break
        page = models.Page.objects.get(id=row[0])
        _log.info("[%s] indexing page: %s" % (count, page.url))
        solr.add(**page.solr_doc)
        count += 1
        if count % 100 == 0:
            reset_queries()
    solr.commit()

def word_matches_for_page(page_id, words):
    """
    Gets a list of pre-analyzed words for a list of words on a particular 
    page. So if you pass in 'manufacturer' you can get back a list like
    ['Manufacturer', 'manufacturers', 'MANUFACTURER'] etc ...
    """
    solr = SolrConnection(settings.SOLR)

    # Make sure page_id is of type str, else the following string
    # operation may result in a UnicodeDecodeError. For example, see
    # ticket #493
    if not isinstance(page_id, str):
        page_id = str(page_id)

    q = 'id:%s AND %s' % (page_id, query_join(words, 'ocr'))
    params = {"hl.snippets": 100, "hl.requireFieldMatch": 'true'} 
    response = solr.query(q, fields=['id'], highlight=['ocr'], **params)
    
    if not response.highlighting.has_key(page_id) or \
        not response.highlighting[page_id].has_key('ocr'):
        return []

    words = set()
    for context in response.highlighting[page_id]['ocr']:
        words.update(find_words(context))
    return list(words)

def commit():
    solr = SolrConnection(settings.SOLR)
    solr.commit()

def _get_sort(sort, in_pages=False):
    sort_field = sort_order = None
    if sort == 'state':
        sort_field = 'country' # odd artifact of Title model
        sort_order = 'asc'
    elif sort == 'title':
        # important to sort on title_facet since it's the original 
        # string, and not the analyzed title 
        sort_field = 'title_normal'
        sort_order = 'asc'
    # sort by the full issue date if we searching pages
    elif sort == 'date' and in_pages:
        sort_field = 'date'
        sort_order = 'asc'
    elif sort == 'date':
        sort_field = 'start_year'
        sort_order = 'asc'
    return sort_field, sort_order

def _expand_ethnicity(e):
    """
    takes an ethnicity string, expands it out the query using the 
    the EthnicitySynonym models, and returns a chunk of a lucene query
    """
    parts = ['subject:"%s"' % e]
    ethnicity = models.Ethnicity.objects.get(name=e)
    for s in ethnicity.synonyms.all():
        parts.append('subject:"%s"' % s.synonym)
    q = ' OR '.join(parts)
    return "(" + q + ")"

def _solrize_date(d, is_start=True):
    """
    Takes a string like 01/01/1900 or 01/1900 or 1900 and returns an
    integer suitable for querying the date field in a solr document.
    The is_start is relevant for determining what date to round to
    when given a partial date like 01/1900 or 1900.
    """
    d = d.strip()

    # 01/01/1900 -> 19000101 ; 1/1/1900 -> 19000101
    match = re.match(r'(\d\d?)/(\d\d?)/(\d{4})', d)
    if match:
        m, d, y = match.groups()
    else:
        # 01/1900 -> 19000101 | 19000131
        match = re.match(r'(\d\d?)/(\d{4})', d)
        if match:
            m, y = match.groups()
            if is_start:
                d = '01'
            else:
                d = '31'
        else:
            # 1900 -> 19000101 | 19001231
            match = re.match('(\d{4})', d)
            if match:
                y = match.group(1)
                if is_start:
                    m, d = '01', '01'
                else:
                    m, d = '12', '31'
            else:
                return None

    if y and m and d:
        return int(y) * 10000 + int(m) * 100 + int(d)
    else:
        return None
