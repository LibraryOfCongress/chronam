import os
import re
import datetime
import urlparse
import wsgiref.util
import calendar

try:
    import simplejson as json
except ImportError:
    import json

import Image

from chronam import settings
from chronam.utils.rfc3339 import rfc3339

try:
    import j2k
except ImportError:
    j2k = None


from django.core.paginator import Paginator, EmptyPage
from django.db import connection
from django.http import HttpResponse, HttpResponseNotFound, Http404, \
                        HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.utils.http import http_date
from django.utils import cache
from django.views.decorators.vary import vary_on_headers
from django.views import static
from django.core import urlresolvers
from django import forms as django_forms
from django.forms import fields
from django.db.models import Count, Max

from chronam.web import models, forms, index
from chronam.web.decorators import rdf_view, opensearch_clean
from chronam import utils
from chronam.settings import THUMBNAIL_WIDTH
from chronam.web.rdf import title_to_graph, issue_to_graph, page_to_graph, \
                            titles_to_graph, batch_to_graph, awardee_to_graph
from chronam.web.json_helper import batch_to_json

def _page_range_short(paginator, page):
    middle = 3
    for p in paginator.page_range:
        if p <= 3:
            yield p
        elif paginator.num_pages - p < 3:
            yield p
        elif abs(p - page.number) < middle:
            yield p
        elif abs(p - page.number) == middle:
            yield "..."


# TODO: refactor me and give me a new home?
class HTMLCalendar(calendar.Calendar):
    """
    This calendar returns complete HTML pages.
    """

    def __init__(self, firstweekday=0, issues=None):
        calendar.Calendar.__init__(self, firstweekday)
        self.issues = issues

    # CSS classes for the day <td>s
    cssclasses = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

    def formatday(self, year, month, day, weekday):
        """
        Return a day as a table cell.
        """
        if day == 0:
            return '<td class="noday">&nbsp;</td>' # day outside month
        else:
            r = self.issues.filter(date_issued=datetime.date(year, month, day))
            issues = set()
            for issue in r:
                issues.add((issue.title.lccn, issue.date_issued, issue.edition))
            issues = sorted(list(issues))            
            count = len(issues)
            if count==1:
                _class = "single"
                lccn, date_issued, edition = issues[0]
                kw = dict(lccn=lccn, date=date_issued, edition=edition)
                url = urlresolvers.reverse('chronam_issue_pages', kwargs=kw)
                _day = """<a href="%s">%s</a>""" % (url, day)
            elif count>1:
                _class = "multiple"
                _day = "%s " % day
                for lccn, date_issued, edition in issues:
                    kw = dict(lccn=lccn, date=date_issued, edition=edition)
                    url = urlresolvers.reverse('chronam_issue_pages', kwargs=kw)
                    _day += """<a href="%s">ed-%d</a>""" % (url, edition)
            else:
                _class = "noissues"
                _day = day
            return '<td class="%s %s">%s</td>' % (_class, self.cssclasses[weekday], _day)

    def formatweek(self, year, month, theweek):
        """
        Return a complete week as a table row.
        """
        s = ''.join(self.formatday(year, month, d, wd) for (d, wd) in theweek)
        return '<tr>%s</tr>' % s

    def formatweekday(self, day):
        """
        Return a weekday name as a table header.
        """
        return '<td class="dayname %s">%s</td>' % (self.cssclasses[day], calendar.day_abbr[day][0])

    def formatweekheader(self):
        """
        Return a header for a week as a table row.
        """
        s = ''.join(self.formatweekday(i) for i in self.iterweekdays())
        return '<tr class="daynames">%s</tr>' % s

    def formatmonthname(self, theyear, themonth, withyear=True):
        """
        Return a month name as a table row.
        """
        if withyear:
            s = '%s %s' % (calendar.month_name[themonth], theyear)
        else:
            s = '%s' % calendar.month_name[themonth]
        return '<tr><td colspan="7" class="title">%s, %s</td></tr>' % (s, theyear)

    def formatmonth(self, theyear, themonth, withyear=True):
        """
        Return a formatted month as a table.
        """
        v = []
        a = v.append
        a('<table border="0" cellpadding="0" cellspacing="0" class="month">')
        a('\n')
        a(self.formatmonthname(theyear, themonth, withyear=withyear))
        a('\n')
        a(self.formatweekheader())
        a('\n')
        weeks = self.monthdays2calendar(theyear, themonth)
        if len(weeks)<6:
            # add blank week so all calendars are 6 weeks long.
            weeks.append([(0, 0)]*7)
        for week in weeks:
            a(self.formatweek(theyear, themonth, week))
            a('\n')
        a('</table>')
        a('\n')
        return ''.join(v)

    def formatyear(self, theyear, width=3):
        """
        Return a formatted year as a table of tables.
        """
        v = []
        a = v.append
        width = max(width, 1)
        a('<div id="calendar"><table>')
        a('\n')
        #a('<tr class="calendar_row">' % (width, theyear))
        for i in range(calendar.January, calendar.January+12, width):
            # months in this row
            months = range(i, min(i+width, 13))
            a('<tr class="calendar_row">')
            for m in months:
                a('<td class="calendar_month">')
                a(self.formatmonth(theyear, m, withyear=False))
                a('</td>')
            a('</tr>')
        a('</table></div>')
        return ''.join(v)

def cache_page(ttl):
    def decorator(function):
        def decorated_function(*args, **kwargs):
            request = args[0]
            response = function(*args, **kwargs)
            cache.patch_response_headers(response, ttl)
            return response
        return decorated_function
    return decorator

@cache_page(settings.DEFAULT_TTL_SECONDS)
def home(request):
    page_title = ""
    letters = [chr(n) for n in range(65,91)]
    return render_to_response('home.html', dictionary=locals(),
                              context_instance=RequestContext(request))
 
@cache_page(settings.DEFAULT_TTL_SECONDS)
def about(request):
    page_title = "About Chronicling America"
    return render_to_response('about.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def help(request):
    page_title = "Help"
    return render_to_response('help.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def ocr(request):
    page_title = "OCR in Chronicling America"
    return render_to_response('ocr.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def about_api(request):
    page_title = "About the Chronicling America API"
    return render_to_response('about_api.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def title(request, lccn):
    title = get_object_or_404(models.Title, lccn=lccn)
    page_title = "About this Newspaper: %s" % unicode(title.name)
    # we call these here, because the query the db, they are not 
    # cached by django's ORM, and we have some conditional logic 
    # in the template that would result in them getting called more
    # than once. Short story: minimize database hits...
    related_titles = title.related_titles()
    succeeding_titles = title.succeeding_titles()
    preceeding_titles = title.preceeding_titles()
    profile_uri = 'http://www.openarchives.org/ore/html/'
    notes = []
    has_external_link = False
    for note in title.notes.all():

        text = re.sub('(http(s)?://[^\s]+[^\.])', r'<a class="external" href="\1">\1</a>', note.text)
        if text!=note.text:
            has_external_link = True
        notes.append(text)
    response = render_to_response('title.html', dictionary=locals(),
                                  context_instance=RequestContext(request))
    return response

@cache_page(settings.DEFAULT_TTL_SECONDS)
def title_atom(request, lccn, page_number=1):
    title = get_object_or_404(models.Title, lccn=lccn)
    issues = title.issues.all().order_by('-batch__released', '-date_issued')
    paginator = Paginator(issues, 100)
    try:
        page = paginator.page(int(page_number))
    except EmptyPage:
        raise Http404("No such page %s for title feed" % page_number)

    # figure out the time the title was most recently updated
    # typically the release date of the batch, otherwise
    # when the batch was ingested 
    issues = page.object_list
    num_issues = issues.count()
    if num_issues > 0:
        if issues[0].batch.released:
            feed_updated = issues[0].batch.released
        else:
            feed_updated = issues[0].batch.created
    else:
        feed_updated = title.created

    host = request.get_host()
    return render_to_response('title.xml', dictionary=locals(),
                              mimetype='application/atom+xml',
                              context_instance=RequestContext(request)) 

def _rdf_base(request):
    host = request.get_host()
    path = request.get_full_path().rstrip(".rdf")
    return "http://%s%s" % (host, path)

@cache_page(settings.DEFAULT_TTL_SECONDS)
@rdf_view
def title_rdf(request, lccn):
    title = get_object_or_404(models.Title, lccn=lccn)
    graph = title_to_graph(title)
    response = HttpResponse(graph.serialize(base=_rdf_base(request), include_base=True), mimetype='application/rdf+xml')
    return response

@cache_page(settings.DEFAULT_TTL_SECONDS)
def title_marc(request, lccn):
    title = get_object_or_404(models.Title, lccn=lccn)
    page_title = "MARC Bibliographic Record: %s" % unicode(title.name)
    return render_to_response('marc.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def title_marcxml(request, lccn):
    title = get_object_or_404(models.Title, lccn=lccn)
    return HttpResponse(title.marc.xml, mimetype='application/marc+xml')

@cache_page(settings.DEFAULT_TTL_SECONDS)
def title_holdings(request, lccn):
    title = get_object_or_404(models.Title, lccn=lccn)
    page_title = "Libraries that Have It: %s" % unicode(title.name)
    holdings = title.holdings.all()

    return render_to_response('holdings.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def essays(request):
    page_title = 'Newspaper Title Essays'
    titles = models.Title.objects.filter(essays__gte=0).distinct()
    titles = titles.order_by('name')
    return render_to_response('essays.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def title_essays(request, lccn):
    title = get_object_or_404(models.Title, lccn=lccn)
    # if there's only one essay might as well redirect to it
    if len(title.essays.all()) == 1:
        url = title.essays.all()[0].url
        return HttpResponseRedirect(url)
    elif len(title.essays.all()) == 0:
        return HttpResponseNotFound("No essays for this title.")
    page_title = "Essays for: %s" % unicode(title)
    return render_to_response('title_essays.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)    
def title_essay(request, lccn, created):
    #fh = open('/home/esummers/foo.log', 'a')
    #fh.write("lccn=%s created=%s\n" % (lccn, created))
    try:
        created = datetime.datetime.strptime(created, '%Y%m%d%H%M%S')
    except:
        raise Http404()
    title = get_object_or_404(models.Title, lccn=lccn)
    essay = title.essays.filter(created=created)[0]
    page_title = "More About This Newspaper: %s" % unicode(title)
    base = request.META['SCRIPT_NAME']
    essay_div = essay.get_div(base)
    return render_to_response('essay.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def issues(request, lccn, year=None):
    title = get_object_or_404(models.Title, lccn=lccn)
    issues = title.issues.all()

    if issues.count()>0:
        if year is None:
            _year = issues[0].date_issued.year
        else:
            _year = int(year)
    else:
        _year = 1900 # no issues available
    year_view = HTMLCalendar(firstweekday=6, issues=issues).formatyear(_year)

    dates = issues.dates('date_issued', 'year')
    class SelectYearForm(django_forms.Form):
        year = fields.ChoiceField(choices=((d.year, d.year) for d in dates), initial=_year)
    select_year_form = SelectYearForm()

    page_title = "Browse Issues: %s" % unicode(title)

    return render_to_response('issues.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def issues_first_pages(request, lccn, page_number=1):
    title = get_object_or_404(models.Title, lccn=lccn)
    issues = title.issues.all()

    first_pages = []
    for issue in issues:
        first_pages.append(issue.first_page)

    try:
        paginator = Paginator(first_pages, 10)
        page = paginator.page(int(page_number))
        page_range_short = list(_page_range_short(paginator, page))
    except EmptyPage:
        raise Http404("No such page %s" % page_number)

    page_title = "Browse Issues: %s" % unicode(title)
    
    return render_to_response('issues_first_pages.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
@rdf_view
def issue_pages_rdf(request, lccn, date, edition):
    title, issue, page = _get_tip(lccn, date, edition)
    graph = issue_to_graph(issue)
    response = HttpResponse(graph.serialize(base=_rdf_base(request), include_base=True), mimetype='application/rdf+xml')
    return response


@cache_page(settings.DEFAULT_TTL_SECONDS)
def issue_pages(request, lccn, date, edition, page_number=1):
    title = get_object_or_404(models.Title, lccn=lccn)
    _year, _month, _day = date.split("-")
    try:
        _date = datetime.date(int(_year), int(_month), int(_day))
    except ValueError, e:
        raise Http404
    try:
        issue = title.issues.filter(date_issued=_date, edition=edition).order_by("-created")[0]
    except IndexError, e:
        raise Http404
    paginator = Paginator(issue.pages.all(), 10)
    page = paginator.page(int(page_number))
    if not page.object_list:
        notes = issue.notes.filter(type="noteAboutReproduction")
        num_notes = notes.count()
        if num_notes>=1:
            explanation = notes[0].text
        else:
            explanation = ""
    page_title = 'All pages for this Issue: %s - %s - edition %s' % (issue.title, issue.date_issued, issue.edition)
    profile_uri = 'http://www.openarchives.org/ore/html/'
    response = render_to_response('issue_pages.html', dictionary=locals(),
                                  context_instance=RequestContext(request))
    return response

   
@cache_page(settings.DEFAULT_TTL_SECONDS)
@vary_on_headers('User-Agent', 'Referer')
def page(request, lccn, date, edition, sequence, words=None):
    title, issue, page = _get_tip(lccn, date, edition, sequence)
    if not page.jp2_filename:
        notes = page.notes.filter(type="noteAboutReproduction")
        num_notes = notes.count()
        if num_notes>=1:
            explanation = notes[0].text
        else:
            explanation = ""

    # if no word highlights were requests, see if the user came 
    # from search engine results and attempt to highlight words from their 
    # query by redirecting to a url that has the highlighted words in it  
    if not words:
        try:
            words = _search_engine_words(request)
            if len(words) > 0:
                words = '+'.join(words)
                path_parts = dict(lccn=lccn, date=date, edition=edition, 
                                  sequence=sequence, words=words)
                url = urlresolvers.reverse('chronam_page_words', kwargs=path_parts)
                return HttpResponseRedirect(url)
        except Exception, e:
            if settings.DEBUG:
                raise e
            # else squish the exception so the page will still get
            # served up minus the highlights

    # Calculate the previous_issue_first_page. Note: it was decided
    # that we want to skip over issues with missing pages. See ticket
    # #383.
    _issue = issue
    while True:
        previous_issue_first_page = None
        _issue = _issue.previous
        if not _issue:
            break
        previous_issue_first_page = _issue.first_page
        if previous_issue_first_page:
            break

    # do the same as above but for next_issue this time.
    _issue = issue
    while True:
        next_issue_first_page = None
        _issue = _issue.next
        if not _issue:
            break
        next_issue_first_page = _issue.first_page
        if next_issue_first_page:
            break

    page_title = "%s" % page

    image_credit = issue.batch.awardee.name
    host = request.get_host()
    bot = _is_search_bot(request.META.get('HTTP_USER_AGENT'))
    profile_uri = 'http://www.openarchives.org/ore/html/'
    response = render_to_response('page.html', dictionary=locals(),
                                  context_instance=RequestContext(request))
    return response

@cache_page(settings.DEFAULT_TTL_SECONDS)
@rdf_view
def page_rdf(request, lccn, date, edition, sequence):
    title, issue, page = _get_tip(lccn, date, edition, sequence)
    graph = page_to_graph(page)
    response = HttpResponse(graph.serialize(base=_rdf_base(request), include_base=True), mimetype='application/rdf+xml')
    return response

def page_pdf(request, lccn, date, edition, sequence):
    title, issue, page = _get_tip(lccn, date, edition, sequence)
    return _stream_file(page.pdf_abs_filename, 'application/pdf')

def page_jp2(request, lccn, date, edition, sequence):
    title, issue, page = _get_tip(lccn, date, edition, sequence)
    return _stream_file(page.jp2_abs_filename, 'image/jp2')

def page_ocr_xml(request, lccn, date, edition, sequence):
    title, issue, page = _get_tip(lccn, date, edition, sequence)
    return _stream_file(page.ocr_abs_filename, 'application/xml')

def page_ocr_txt(request, lccn, date, edition, sequence):
    title, issue, page = _get_tip(lccn, date, edition, sequence)
    return HttpResponse(page.ocr.text, mimetype='text/plain')

@cache_page(settings.DEFAULT_TTL_SECONDS)
def coordinates(request, lccn, date, edition, sequence, words=None):
    title, issue, page = _get_tip(lccn, date, edition, sequence)
    try:
        ocr = page.ocr
    except models.OCR.DoesNotExist, e:
        ocr = None
    if ocr is None:
        r = HttpResponseNotFound()
        r.write("page has no ocr")
        return r
    if words is not None:
        word_coordinates = ocr.word_coordinates
        all_coordinates = {}
        for word in words.split("+"):
            if word:
                all_coordinates[word] = word_coordinates.get(word, [])
        return HttpResponse(json.dumps(all_coordinates),
                            mimetype='application/json')
    else:
        r = HttpResponse(mimetype='application/json')
        r.write(str(ocr.word_coordinates_json))
        return r

@cache_page(settings.DEFAULT_TTL_SECONDS)
def page_print(request, lccn, date, edition, sequence, width, height, x1, y1, x2, y2):
    title, issue, page = _get_tip(lccn, date, edition, sequence)
    page_title = str(title)
    host = request.get_host()
    image_credit = issue.batch.awardee.name
    return render_to_response('page_print.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def page_ocr(request, lccn, date, edition, sequence):
    title, issue, page = _get_tip(lccn, date, edition, sequence)
    page_title = str(title)
    host = request.get_host()
    return render_to_response('page_text.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def search_pages_opensearch(request):
    host = request.get_host()
    return render_to_response('search_pages_opensearch.xml',
            mimetype='application/opensearchdescription+xml',
            dictionary=locals(), context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def search_pages(request):
    search_form = forms.SearchPagesForm()
    page_title = 'Search Newspaper Pages'
    return render_to_response('search_pages.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
@opensearch_clean
def search_pages_results(request, view_type=None):
    crumbs = [
        {'label':'Search Newspaper Pages', 
         'href': urlresolvers.reverse('chronam_search_pages') }, 
        ]
    try:
        curr_page = int(request.REQUEST.get('page', 1))
    except ValueError, e:
        curr_page = 1

    page_title = "Page Search Results"
    paginator = index.SolrPaginator(request.GET)

    try:
        page = paginator.page(curr_page)
    except EmptyPage:
        url = urlresolvers.reverse('chronam_search_pages_results')
        query = request.GET.copy() 
        # Set the page to the last page
        query['page'] = paginator.num_pages
        return HttpResponseRedirect('%s?%s' % (url, query.urlencode()) )

    # figure out the next page number
    query = request.GET.copy()
    if page.has_next():
        query['page'] = curr_page + 1
        next_url = '?' + query.urlencode()

    # and the previous page number
    if page.has_previous():
        query['page'] = curr_page - 1
        previous_url = '?' + query.urlencode()


    host = request.get_host()
    format = request.GET.get('format', None)
    if format == 'atom':
        feed_url = 'http://' + host + request.get_full_path()
        updated = rfc3339(datetime.datetime.now())
        return render_to_response('search_pages_results.xml',
                                  dictionary=locals(), 
                                  context_instance=RequestContext(request),
                                  mimetype='application/atom+xml')

    elif format == 'json':
        results = [p.solr_doc for p in page.object_list]
        return HttpResponse(json.dumps(results, indent=2), 
                            mimetype='application/json')

    page_range_short = list(_page_range_short(paginator, page))

    # copy the current request query without the page and sort
    # query params so we can construct links with it in the template
    q = request.GET.copy()
    if q.has_key('page'):
        del q['page']
    if q.has_key('sort'):
        del q['sort']
    q = q.urlencode()

    # get an pseudo english version of the query
    english_search = paginator.englishify()

    # get some stuff from the query string for use in the form
    lccns = query.getlist('lccn')
    states = query.getlist('state')

    # c'mon humor me, ok
    if request.GET.get('phrasetext', '').lower() == 'rick astley rickroll':
        return HttpResponseRedirect('http://www.youtube.com/watch?v=oHg5SJYRHA0')

    # figure out the sort that's in use
    sort = query.get('sort', 'relevance')
    if view_type=="list":
        template = "search_pages_results_list.html"
    else:
        template = "search_pages_results_thumbnail.html"
    return render_to_response(template, dictionary=locals(),
                              context_instance=RequestContext(request))  

@cache_page(settings.DEFAULT_TTL_SECONDS)
def search_titles_opensearch(request):
    host = request.get_host()
    return render_to_response('search_titles_opensearch.xml',
            mimetype='application/opensearchdescription+xml',
            dictionary=locals(), context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def search_titles(request):
    page_title = 'Search Newspaper Directory'
    ethnicities = models.Ethnicity.objects.all()
    labor_presses = models.LaborPress.objects.all()
    languages = models.Language.objects.all()
    material_types = models.MaterialType.objects.all()
    return render_to_response('search_titles.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
@opensearch_clean
def search_titles_results(request):
    crumbs = [
        {'label':'Search Newspaper Directory', 
         'href': urlresolvers.reverse('chronam_search_titles') }, 
        ]
    page_title = 'Title Search Results'

    try:
        curr_page = int(request.REQUEST.get('page', 1))
    except ValueError, e:
        curr_page = 1

    paginator = index.SolrTitlesPaginator(request.GET)

    try:
        page = paginator.page(curr_page)
    except:
        raise Http404

    page_range_short = list(_page_range_short(paginator, page))

    query = request.GET.copy()
    if page.has_next():
        query['page'] = curr_page + 1
        next_url = '?' + query.urlencode()
    if page.has_previous():
        query['page'] = curr_page - 1
        previous_url = '?' + query.urlencode()

    host = request.get_host()
    format = request.GET.get('format', None)
    if format == 'atom':
        feed_url = 'http://' + host + request.get_full_path()
        updated = rfc3339(datetime.datetime.now())
        return render_to_response('search_titles_results.xml',
                                  dictionary=locals(), 
                                  context_instance=RequestContext(request),
                                  mimetype='application/atom+xml')

    elif format == 'json':
        results = [t.solr_doc for t in page.object_list]
        return HttpResponse(json.dumps(results), mimetype='application/json')

    sort = request.GET.get('sort', 'relevance')

    q = request.GET.copy()
    if q.has_key('page'):
        del q['page']
    if q.has_key('sort'):
        del q['sort']
    q = q.urlencode()
    return render_to_response('search_titles_results.html', dictionary=locals(),
                               context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def newspapers(request, state=None, format='html'):
    titles = models.Title.objects.distinct().filter(issues__isnull=False)
    if state:
        template = 'newspapers_state'
        state = utils.unpack_url_path(state)
        titles = titles.filter(country__name=state)
        if titles.count()==0:
            raise Http404
        page_title = '%s Newspapers' % state
        crumbs = [
            {'label':'See All Available Newspapers', 
             'href': urlresolvers.reverse('chronam_newspapers') }, 
            ]
        q = models.Issue.objects.filter(title__in=titles)
        q = q.aggregate(Count('pages'))
        number_of_pages = q['pages__count']
    else:
        template = 'newspapers'
        titles = titles.order_by('country__name', 'name_normal')
        states = set()
        for title in titles:
            states.add(title.country.name)
        states = sorted(states)
        page_title = 'See All Available Newspapers'
        number_of_pages=index.page_count()
    if format=="txt":
        host = request.get_host()
        return render_to_response("%s.%s" % (template, format), 
                                  dictionary=locals(),
                                  context_instance=RequestContext(request), 
                                  mimetype="text/plain")
    else:
        return render_to_response("%s.%s" % (template, format), 
                                  dictionary=locals(),
                                  context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def newspapers_atom(request):
    # get a list of titles with issues that are in order by when they 
    # were last updated
    titles = models.Title.objects.filter(issues__isnull=False).annotate(last_release=Max('issues__batch__released'))
    titles = titles.distinct().order_by('-last_release')

    # get the last update time for all the titles to use as the 
    # updated time for the feed
    if titles.count() > 0:
        last_issue = titles[0].last_issue_released
        if last_issue.batch.released: 
            feed_updated = last_issue.batch.released
        else:
            feed_updated = last_issue.batch.created
    else:
        feed_updated = datetime.datetime.now()

    host = request.get_host()
    return render_to_response("newspapers.xml", dictionary=locals(),
                              mimetype="application/atom+xml",
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
@rdf_view
def newspapers_rdf(request):
    titles = models.Title.objects.distinct().filter(issues__isnull=False)
    graph = titles_to_graph(titles)
    return HttpResponse(graph.serialize(base=_rdf_base(request), include_base=True), mimetype='application/rdf+xml')

if not j2k:
    def _thumbnail(issue, page, out):
        filename = page.tiff_abs_filename
        if not filename:
            raise Http404

        try:
            im = Image.open(filename)
        except IOError:
            raise Http404

        width, height = im.size
        thumb_width = THUMBNAIL_WIDTH
        thumb_height = int(float(thumb_width)/width*height)
        f = im.resize((thumb_width, thumb_height), Image.ANTIALIAS)
        f.save(out, "JPEG")
else:
    def _thumbnail(issue, page, out):
        filename = page.jp2_abs_filename
        if not filename:
            raise Http404

        width, height = page.jp2_width, page.jp2_length
        thumb_width = THUMBNAIL_WIDTH
        thumb_height = int(float(thumb_width)/width*height) 

        try:
            rows, cols, nChannels, bpp, data = j2k.raw_image(filename, 
                                                         int(2*thumb_width), 
                                                         int(2*thumb_height))
        except IOError:
            raise Http404

        im = Image.frombuffer("L", (cols, rows), data, "raw", "L", 0, 1)
        im = im.resize((thumb_width, thumb_height), Image.ANTIALIAS) 
        im.save(out, "JPEG")

@cache_page(settings.PAGE_IMAGE_TTL_SECONDS)
def thumbnail(request, lccn, date, edition, sequence):
    """
    
    """
    title, issue, page = _get_tip(lccn, date, edition, sequence)
    response = HttpResponse(mimetype="image/jpeg")
    _thumbnail(issue, page, response)
    return response

@cache_page(settings.PAGE_IMAGE_TTL_SECONDS)
def page_image(request, lccn, date, edition, sequence, width, height):
    title, issue, page = _get_tip(lccn, date, edition, sequence)
    return page_image_tile(request, lccn, date, edition, sequence,
                           width, height, 0, 0, page.jp2_width, page.jp2_length)

@cache_page(settings.PAGE_IMAGE_TTL_SECONDS)
def page_image_tile(request, lccn, date, edition, sequence,
                    width, height, x1, y1, x2, y2):
    title, issue, page = _get_tip(lccn, date, edition, sequence)
    response = HttpResponse(mimetype="image/jpeg")

    width, height = int(width), int(height)
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

    if not j2k:
        filename = page.tiff_abs_filename
        try:
            im = Image.open(filename)
        except IOError:
            raise Http404
        c = im.crop(x1, y1, x2, y2)
        f = c.resize((width, height))
        f.save(response, "JPEG")
    else:
        filename = page.jp2_abs_filename
        r = j2k.image_tile(filename, width, height, x1, y1, x2, y2)
        response.write(r)
    return response

@cache_page(settings.DEFAULT_TTL_SECONDS)
def batches(request):
    page_title = 'Batches'
    batches = models.Batch.objects.all().order_by('-created')
    return render_to_response('batches.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def batches_atom(request):
    batches = models.Batch.objects.all().order_by('-released')
    now = rfc3339(datetime.datetime.now())
    return render_to_response('batches.xml', dictionary=locals(),
                              context_instance=RequestContext(request),
                              mimetype='application/atom+xml')

@cache_page(settings.DEFAULT_TTL_SECONDS)
def batches_json(request):
    batches = models.Batch.objects.all().order_by('-created')
    j = [batch_to_json(b, serialize=False) for b in batches]
    return HttpResponse(json.dumps(j, indent=2), mimetype='application/json')

@cache_page(settings.DEFAULT_TTL_SECONDS)
def batch(request, batch_name):
    batch = get_object_or_404(models.Batch, name=batch_name)
    page_title = 'Batch: %s' % batch.name
    profile_uri = 'http://www.openarchives.org/ore/html/'
    return render_to_response('batch.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
@rdf_view
def batch_rdf(request, batch_name):
    batch = get_object_or_404(models.Batch, name=batch_name)
    graph = batch_to_graph(batch)
    response = HttpResponse(graph.serialize(base=_rdf_base(request), include_base=True), mimetype='application/rdf+xml')
    return response

@cache_page(settings.DEFAULT_TTL_SECONDS)
def batch_json(request, batch_name):
    batch = get_object_or_404(models.Batch, name=batch_name)
    return HttpResponse(batch_to_json(batch), mimetype='application/json')

@cache_page(settings.DEFAULT_TTL_SECONDS)
def event(request, event_id):
    page_title = 'Event'
    event = get_object_or_404(models.LoadBatchEvent, id=event_id)
    return render_to_response('event.html', dictionary=locals(),
                             context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def events(request):
    page_title = 'Events'
    events = models.LoadBatchEvent.objects.all().order_by('-created')
    return render_to_response('events.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def events_atom(request):
    events = models.LoadBatchEvent.objects.all().order_by('-created')
    return render_to_response('events.xml', dictionary=locals(),
                              context_instance=RequestContext(request),
                              mimetype='application/atom+xml')

@cache_page(settings.DEFAULT_TTL_SECONDS)
def titles(request, start=None, page_number=1):
    page_title = 'Newspaper Titles'
    if start:
        page_title += ' Starting With %s' % start
        titles = models.Title.objects.order_by('name_normal').filter(name_normal__istartswith=start.upper())
    else:
        titles = models.Title.objects.all().order_by('name_normal')
    paginator = Paginator(titles, 50)
    page = paginator.page(int(page_number))
    page_range_short = list(_page_range_short(paginator, page))
    letters = [chr(n) for n in range(65,91)]

    return render_to_response('titles.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def titles_in_city(request, state, county, city, page_number=1, order='name_normal'):
    state, county, city = map(utils.unpack_url_path, (state, county, city))
    page_title = "Titles in City: %s, %s" % (city, state)
    titles = models.Title.objects.filter(places__city=city,
                                         places__county=county, 
                                         places__state=state).order_by(order)
    if titles.count()==0:
        raise Http404

    paginator = Paginator(titles, 50)
    page = paginator.page(int(page_number))
    page_range_short = list(_page_range_short(paginator, page))

    state, county, city = map(utils.pack_url_path, (state, county, city))
    return render_to_response('city.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def titles_in_county(request, state, county, page_number=1, order='name_normal'):
    state, county = map(utils.unpack_url_path, (state, county))
    page_title = "Titles in County: %s, %s" % (county, state)
    titles = models.Title.objects.filter(places__county=county,
                                         places__state=state).distinct()
    if titles.count()==0:
        raise Http404

    paginator = Paginator(titles, 50)
    page = paginator.page(int(page_number))
    page_range_short = list(_page_range_short(paginator, page))

    state, county = map(utils.pack_url_path, (state, county))
    return render_to_response('county.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def titles_in_state(request, state, page_number=1, order='name_normal'):
    state = utils.unpack_url_path(state)
    page_title = "Titles in State: %s" % state
    titles = models.Title.objects.order_by(order).filter(places__state=state).distinct()

    if titles.count()==0:
        raise Http404

    paginator = Paginator(titles, 50)
    page = paginator.page(int(page_number))
    page_range_short = list(_page_range_short(paginator, page))

    state = utils.pack_url_path(state)
    return render_to_response('state.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.DEFAULT_TTL_SECONDS)
def states(request, format='html'):
    page_title = 'States'
    # custom SQL to eliminate spelling errors and the like in cataloging data
    # TODO: maybe use Django ORM once the data is cleaned more on import
    cursor = connection.cursor()
    cursor.execute("SELECT state, COUNT(*) AS count FROM places WHERE state IS NOT NULL GROUP BY state HAVING count > 10 ORDER BY state")
    if format == 'json' or request.META['HTTP_ACCEPT'] == 'application/json':
        states = [n[0] for n in cursor.fetchall()]
        states.extend(["----------------", "American Samoa", 
                       "Mariana Islands", "Puerto Rico", "Virgin Islands"])
        return HttpResponse(json.dumps(states),
                            mimetype='application/json')
    states = [(n[0], utils.pack_url_path(n[0])) for n in cursor.fetchall()]
    return render_to_response('states.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def counties_in_state(request, state, format='html'):
    state = utils.unpack_url_path(state)
    page_title = 'Counties in %s' % state

    places = models.Place.objects.filter(state=state, 
                                         county__isnull=False).all()
    county_names = sorted(set(p.county for p in places))

    if format == 'json':
        return HttpResponse(json.dumps(county_names),
                            mimetype='application/json')
    counties = [{'name': name, 'abbr': utils.pack_url_path(name)} 
                for name in county_names]
    if len(counties)==0:
        raise Http404
    state_abbr = utils.pack_url_path(state)
    return render_to_response('counties.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def states_counties(request, format='html'):
    page_title = 'Counties by State'

    cursor = connection.cursor()

    cursor.execute("SELECT state, county, COUNT(*) AS total FROM places WHERE state IS NOT NULL AND county IS NOT NULL GROUP BY state, county HAVING total >= 1 ORDER BY state, county")

    states_counties = [(n[0], n[1], n[2]) for n in cursor.fetchall()]

    return render_to_response('states_counties.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def cities_in_county(request, state, county, format='html'):
    state, county = map(utils.unpack_url_path, (state, county))
    page_title = 'Cities in %s, %s' % (state, county)
    places = models.Place.objects.filter(state=state, county=county).all()
    cities = [p.city for p in places]
    if None in cities: 
        cities.remove(None)
    if len(cities)==0:
        raise Http404
    if format == 'json':
        return HttpResponse(json.dumps(cities),
                            mimetype='application/json')
    return render_to_response('cities.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def cities_in_state(request, state, format='html'):
    state = utils.unpack_url_path(state)
    page_title = 'Cities in %s' % state

    places = models.Place.objects.filter(state=state, 
                                         city__isnull=False).all()
    cities = sorted(set(p.city for p in places))

    if len(cities)==0:
        raise Http404
    if format == 'json':
        return HttpResponse(json.dumps(cities),
                            mimetype='application/json')
    return render_to_response('cities.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def institutions(request, page_number=1):
    page_title = 'Institutions'
    institutions = models.Institution.objects.all()
    paginator = Paginator(institutions, 50)
    page = paginator.page(int(page_number))
    page_range_short = list(_page_range_short(paginator, page))
    return render_to_response('institutions.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def institution(request, code):
    institution = get_object_or_404(models.Institution, code=code)
    page_title = institution
    titles_count = models.Title.objects.filter(holdings__institution=institution).distinct().count()
    holdings_count = models.Holding.objects.filter(institution=institution).count()
    return render_to_response('institution.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def institution_titles(request, code, page_number=1):
    institution = get_object_or_404(models.Institution, code=code)
    page_title = 'Titles held by %s' % institution
    titles = models.Title.objects.filter(holdings__institution=institution).distinct()
    paginator = Paginator(titles, 50)
    page = paginator.page(int(page_number))
    page_range_short = list(_page_range_short(paginator, page))
    return render_to_response('institution_titles.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(10)
def status(request):
    page_title = 'System Status'
    page_count = models.Page.objects.all().count()
    issue_count = models.Issue.objects.all().count()
    batch_count = models.Batch.objects.all().count()
    title_count = models.Title.objects.all().count()
    batch_count = models.Batch.objects.all().count()
    holding_count = models.Holding.objects.all().count()
    essay_count = models.Essay.objects.all().count()
    pages_indexed = index.page_count()
    titles_indexed = index.title_count()
    return render_to_response('status.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def awardees(request):
    page_title = 'Awardees'
    awardees = models.Awardee.objects.all().order_by('name')
    return render_to_response('awardees.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def awardee(request, institution_code):
    awardee = get_object_or_404(models.Awardee, org_code=institution_code)
    page_title = 'Awardee: %s' % awardee.name
    batches = models.Batch.objects.filter(awardee=awardee)
    return render_to_response('awardee.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
@rdf_view
def awardee_rdf(request, institution_code):
    awardee = get_object_or_404(models.Awardee, org_code=institution_code)
    graph = awardee_to_graph(awardee)
    response = HttpResponse(graph.serialize(base=_rdf_base(request), include_base=True), mimetype='application/rdf+xml')
    return response

@cache_page(settings.DEFAULT_TTL_SECONDS)
def terms(request):
    return render_to_response('terms.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def omniture(request):
    return static.serve(request, request.path, document_root=settings.STATIC)

@cache_page(settings.DEFAULT_TTL_SECONDS)
def pages_on_flickr(request):
    page_title = "Flickr Report"
    flickr_urls = models.FlickrUrl.objects.all().order_by('-created')
    if len(flickr_urls) > 0:
        last_update = flickr_urls[0].created
    else:
        last_update = None
    return render_to_response('pages_on_flickr.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def batch_summary(request, format='html'):
    page_title = "Batch Summary"
    cursor = connection.cursor()
    cursor.execute("select batches.name, issues.title_id, min(date_issued), max(date_issued), count(pages.id) from batches, issues, pages where batches.name=issues.batch_id and issues.id=pages.issue_id group by batches.name, issues.title_id order by batches.name;")
    batch_details = cursor.fetchall()
    if format == 'txt':
        return render_to_response('batch_summary.txt', dictionary=locals(),
                                  context_instance=RequestContext(request),
                                  mimetype="text/plain")
    return render_to_response('batch_summary.html', 
                              dictionary=locals(),
                              context_instance=RequestContext(request))
 
@cache_page(settings.DEFAULT_TTL_SECONDS)
def reels(request):
    page_title = 'Reels'
    reels = models.Reel.objects.all().order_by('number')
    return render_to_response('reels.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def reel(request, reel_number):
    crumbs = [
        {'label':'Reels', 
         'href': urlresolvers.reverse('chronam_reels') }, 
        ]
    page_title = 'Reel %s' % reel_number
    reel = models.Reel.objects.get(number=reel_number)
    return render_to_response('reel.html', dictionary=locals(),
                              context_instance=RequestContext(request))

def _get_tip(lccn, date, edition, sequence=1):
    """a helper function to lookup a particular page based on metadata cooked
    into the chronam URLs, and raise a 404 appropriately when portions of the
    hiearchical metadata are not found in the database
    """
    title = get_object_or_404(models.Title, lccn=lccn)
    _year, _month, _day = date.split("-")
    try:
        _date = datetime.date(int(_year), int(_month), int(_day))
    except ValueError, e:
        raise Http404
    try:
        issue = title.issues.filter(date_issued=_date, edition=edition).order_by("-created")[0]
    except IndexError, e:
        raise Http404
    try:
        page = issue.pages.filter(sequence=int(sequence)).order_by("-created")[0]
    except IndexError, e:
        raise Http404
    return title, issue, page

       
def _stream_file(path, mimetype):
    """helper function for streaming back the contents of a file"""
    # must calculate Content-length else django ConditionalGetMiddleware 
    # tries to and fails, since it is streaming back, and it attempts to 
    # calculate len() on the response content!
    if path:
        stat = os.stat(path)
        r = HttpResponse(wsgiref.util.FileWrapper(file(path)))
        r['Content-Type'] = mimetype
        r['Content-Length'] = stat.st_size
        r['Last-Modified'] = http_date(stat.st_mtime)
        return r
    else:
        raise Http404

def _is_search_bot(ua):
    if not ua:
        return False

    ua = ua.lower()
    if 'googlebot' in ua:
        return True
    elif 'slurp' in ua:
        return True
    elif 'msnbot' in ua:
        return True
    return False

def _search_engine_words(request):
    """
    Inspects the http request and returns a list of words from the OCR
    text relevant to a particular search engine query. If the
    request didn't come via a search engine result an empty list is
    returned.
    """
    # get the refering url
    referer = request.META.get('HTTP_REFERER')
    if not referer:
        return []
    uri = urlparse.urlparse(referer)
    qs = urlparse.parse_qs(uri.query)

    # extract a potential search query from refering url
    if qs.has_key('q'): # google and microsoft
        words = qs['q'][0]
    elif qs.has_key('p'): # yahoo
        words = qs['p'][0]
    else:
        return []

    # ask solr for the pre-analysis words that could potentially 
    # match on the page. For example if we feed in 'buildings' we could get
    # ['building', 'buildings', 'BUILDING', 'Buildings'] depending
    # on the actual OCR for the page id that is passed in
    words = words.split(' ')
    words = index.word_matches_for_page(request.path, words)

    return words


