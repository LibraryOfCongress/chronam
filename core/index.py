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

_log = logging.getLogger(__name__)

PROX_DISTANCE_DEFAULT = 5

# Incorporated from this thread
# http://groups.google.com/group/solrpy/browse_thread/thread/f4437b885ecb0037?pli=1


ESCAPE_CHARS_RE = re.compile(r'(?<!\\)(?P<char>[&|+\-!(){}[\]^"~*?:])')

def solr_escape(value):
    """
    Escape un-escaped special characters and return escaped value.
    >>> solr_escape(r'foo+') == r'foo\+'
    True
    >>> solr_escape(r'foo\+') == r'foo\+'
    True
    >>> solr_escape(r'foo\\+') == r'foo\\+'
    True
    """
    return ESCAPE_CHARS_RE.sub(r'\\\g<char>', value)

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

        # remove words from query as it's not part of the solr query.
        if 'words' in self.query:
            del self.query['words']

        self._q = page_search(self.query)

        try:
            self._cur_page = int(self.query.get('page'))
        except:
            self._cur_page = 1  # _cur_page is 1-based

        try:
            self._cur_index = int(self.query.get('index'))
        except:
            self._cur_index = 0

        try:
            rows = int(self.query.get('rows'))
        except:
            rows = 10

        # set up some bits that the Paginator expects to be able to use
        Paginator.__init__(self, None, per_page=rows, orphans=0)

        self.overall_index = (self._cur_page - 1) * self.per_page + self._cur_index

        self._ocr_list = ['ocr',]
        self._ocr_list.extend(['ocr_%s' % l for l in settings.SOLR_LANGUAGES])

    def _get_count(self):
        "Returns the total number of objects, across all pages."
        if self._count is None:
            solr = SolrConnection(settings.SOLR) # TODO: maybe keep connection around?
            solr_response = solr.query(self._q, fields=['id'])
            self._count = int(solr_response.results.numFound)
        return self._count
    count = property(_get_count)

    def highlight_url(self, url, words, page, index):
        q = self.query.copy()
        q["words"] = " ".join(words)
        q["page"] = page
        q["index"] = index
        return url + "#" + q.urlencode()

    def _get_previous(self):
        previous_overall_index = self.overall_index - 1
        if previous_overall_index >= 0:
            p_page = previous_overall_index / self.per_page + 1
            p_index = previous_overall_index % self.per_page
            o = self.page(p_page).object_list[p_index]
            q = self.query.copy()
            return self.highlight_url(o.url, o.words, p_page, p_index)
        else:
            return None
    previous_result = property(_get_previous)

    def _get_next(self):
        next_overall_index = self.overall_index + 1
        if next_overall_index < self.count:
            n_page = next_overall_index / self.per_page + 1
            n_index = next_overall_index % self.per_page
            o = self.page(n_page).object_list[n_index]
            return self.highlight_url(o.url, o.words, n_page, n_index)
        else:
            return None
    next_result = property(_get_next)

    def page(self, number):
        """
        Override the page method in Paginator since Solr has already
        paginated stuff for us.
        """

        number = self.validate_number(number)

        # figure out the solr query and execute it
        solr = SolrConnection(settings.SOLR) # TODO: maybe keep connection around?
        start = self.per_page * (number - 1)
        params = {"hl.snippets": 100, # TODO: make this unlimited
            "hl.requireFieldMatch": 'true', # limits highlighting slop
            "hl.maxAnalyzedChars": '102400', # increased from default 51200
            }
        sort_field, sort_order = _get_sort(self.query.get('sort'), in_pages=True)
        solr_response = solr.query(self._q,
                                   fields=['id', 'title', 'date', 'month', 'day',
                                           'sequence', 'edition_label', 
                                           'section_label'],
                                   highlight=self._ocr_list,
                                   rows=self.per_page,
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
            for ocr in self._ocr_list:
                for s in coords.get(ocr) or []:
                    words.update(find_words(s))
            page.words = sorted(words, key=lambda v: v.lower())

            page.highlight_url = self.highlight_url(page.url,
                                                    page.words,
                                                    number, len(pages))
            pages.append(page)

        return Page(pages, number, self)

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
            parts.append(d['proxtext'])
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
        page = self.page(self._cur_page)
        objects = page.object_list
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
        q, fields, sort_field, sort_order = get_solr_request_params_from_query(self.query)

        try:
            page = int(self.query.get('page'))
        except:
            page = 1

        try:
            rows = int(self.query.get('rows'))
        except:
            rows = 50
        start = rows * (page - 1)

        # execute query
        solr_response = execute_solr_query(q, fields, sort_field, sort_order, rows, start)

        # convert the solr documents to Title models
        # could use solr doc instead of going to db, if performance requires it
        results = get_titles_from_solr_documents(solr_response)

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


def get_titles_from_solr_documents(solr_response):
    """
    solr_response: search result returned from SOLR in response to
    title search.

    This function turns SOLR documents into chronam.models.Title 
    instances 
    """
    lccns = [d['lccn'] for d in solr_response.results]
    results = []
    for lccn in lccns:
        try:
            title = models.Title.objects.get(lccn=lccn)
            results.append(title)
        except models.Title.DoesNotExist, e:
            pass # TODO: log exception
    return results


def get_solr_request_params_from_query(query):
    q = title_search(query)
    fields = ['id', 'title', 'date', 'sequence', 'edition_label', 'section_label']
    sort_field, sort_order = _get_sort(query.get('sort'))
    return q, fields, sort_field, sort_order
 

def execute_solr_query(query, fields, sort, sort_order, rows, start):
    solr = SolrConnection(settings.SOLR) # TODO: maybe keep connection around?
    solr_response = solr.query(query,
                               fields=['lccn', 'title',
                                       'edition',
                                       'place_of_publication',
                                       'start_year', 'end_year',
                                       'language'],
                               rows=rows,
                               sort=sort,
                               sort_order=sort_order,
                               start=start)
    return solr_response

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
        q.append('+(title:"%s" OR essay:"%s" OR note:"%s" OR edition:"%s" OR place_of_publication:"%s" OR url:"%s" OR publisher:"%s")' % (term, term, term, term, term, term, term))
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
    if d.get('material_type'):
        q.append('+holding_type:"%s"' % d['material_type'])
    q = ' '.join(q)
    return q


def page_search(d):
    """
    Pass in form data for a given page search, and get back
    a corresponding solr query.
    """
    de = d
    q = ['+type:page']

    if d.get('lccn', None):
        q.append(query_join(d.getlist('lccn'), 'lccn'))

    if d.get('state', None):
        q.append(query_join(d.getlist('state'), 'state'))

    date_filter_type = d.get('dateFilterType', None)
    if date_filter_type == 'year' and d.get('year', None):
        q.append('+date:[%(year)s0101 TO %(year)s1231]' % d)
    elif date_filter_type in ('range', 'yearRange') and d.get('date1', None) \
        and d.get('date2', None):
        d1 = _solrize_date(d['date1'])
        d2 = _solrize_date(d['date2'], is_start=False)
        if d1 and d2:
            q.append('+date:[%i TO %i]' % (d1, d2))
    ocrs = ['ocr_%s' % l for l in settings.SOLR_LANGUAGES]

    lang = d.get('language', None)
    ocr_lang = 'ocr_' + lang if lang else 'ocr'
    if d.get('ortext', None):
        q.append('+((' + query_join(solr_escape(d['ortext']).split(' '), "ocr"))
        if lang:
            q.append(' AND ' + query_join(solr_escape(d['ortext']).split(' '), ocr_lang))
            q.append(') OR ' + query_join(solr_escape(d['ortext']).split(' '), ocr_lang))
        else:
            q.append(')')
            for ocr  in ocrs:
                q.append('OR ' + query_join(solr_escape(d['ortext']).split(' '), ocr))
        q.append(')')
    if d.get('andtext', None):
        q.append('+((' + query_join(solr_escape(d['andtext']).split(' '), "ocr", and_clause=True))
        if lang:
            q.append('AND ' + query_join(solr_escape(d['andtext']).split(' '), ocr_lang, and_clause=True))
            q.append(') OR ' + query_join(solr_escape(d['andtext']).split(' '), ocr_lang, and_clause=True))
        else:
            q.append(')')
            for ocr in ocrs:
                q.append('OR ' + query_join(solr_escape(d['andtext']).split(' '), ocr, and_clause=True))
        q.append(')')
    if d.get('phrasetext', None):
        phrase = solr_escape(d['phrasetext'])
        q.append('+((' + 'ocr' + ':"%s"^10000' % (phrase))
        if lang:
            q.append('AND ocr_' + lang + ':"%s"' % (phrase))
            q.append(') OR ocr_' + lang + ':"%s"' % (phrase))
        else:
            q.append(')')
            for ocr in ocrs:
                q.append('OR ' + ocr + ':"%s"' % (phrase))
        q.append(')')

    if d.get('proxtext', None):
        distance = d.get('proxdistance', PROX_DISTANCE_DEFAULT)
        prox = solr_escape(d['proxtext'])
        q.append('+((' + 'ocr' + ':("%s"~%s)^10000' % (prox, distance))
        if lang:
            q.append('AND ocr_' + lang + ':"%s"~%s' % (prox, distance))
            q.append(') OR ocr_' + lang + ':"%s"~%s' % (prox, distance))
        else:
            q.append(')')
            for ocr in ocrs:
                q.append('OR ' + ocr + ':"%s"~%s' % (prox, distance))
        q.append(')')
    if d.get('sequence', None):
        q.append('+sequence:"%s"' % d['sequence'])
    if d.get('issue_date', None):
        q.append('+month:%d +day:%d' % (int(d['date_month']), int(d['date_day'])))
    return ' '.join(q)

def query_join(values, field, and_clause=False):
    """
    helper to create a chunk of a lucene query, based on
    some value(s) extracted from form data
    """

    # might be single value or a list of values
    if not isinstance(values, list):
        values = [values]

    # escape solr chars
    values = [solr_escape(v) for v in values]

    # quote values
    values = ['"%s"' % v for v in values]

    # add + to the beginnging of each value if we are doing an AND clause
    if and_clause:
        values = ["+%s" % v for v in values]

    # return the lucene query chunk
    if field.startswith("ocr"):
        if field == "ocr":
            return "%s:(%s)^10000" % (field, ' '.join(values))
        else:
            return "%s:(%s)" % (field, ' '.join(values))
    else:
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
        cursor.execute("SELECT lccn FROM core_title WHERE created >= '%s'" % since)
    else:
        solr.delete_query('type:title')
        cursor.execute("SELECT lccn FROM core_title")

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
    cursor.execute("SELECT id FROM core_page")
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

    ocr_list = ['ocr',]
    ocr_list.extend(['ocr_%s' % l for l in settings.SOLR_LANGUAGES])
    ocrs = ' OR '.join([query_join(words, o) for o in ocr_list])
    q = 'id:%s AND (%s)' % (page_id, ocrs)
    params = {"hl.snippets": 100, "hl.requireFieldMatch": 'true', "hl.maxAnalyzedChars": '102400'}
    response = solr.query(q, fields=['id'], highlight=ocr_list, **params)

    if not response.highlighting.has_key(page_id):
        return []

    words = set()
    for ocr in ocr_list:
        if ocr in response.highlighting[page_id]:
            for context in response.highlighting[page_id][ocr]:
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
