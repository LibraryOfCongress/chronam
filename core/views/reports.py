import os
import re
from rfc3339 import rfc3339
import json, datetime

from django.conf import settings
from django.core import urlresolvers
from django.db.models import Min, Max, Count
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import get_template
from django.core.paginator import Paginator, InvalidPage
from django.db import connection
from django.utils import datetime_safe

from chronam.core import index, models
from chronam.core.models import batch_to_json
from chronam.core.rdf import batch_to_graph, awardee_to_graph
from chronam.core.utils.url import unpack_url_path
from chronam.core.decorator import cache_page, rdf_view
from chronam.core.utils.utils import _page_range_short, _rdf_base


@cache_page(settings.API_TTL_SECONDS)
def reports(request):
    page_title = 'Reports'
    return render_to_response('reports/reports.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
def batches(request, page_number=1):
    page_title = 'Batches'
    if settings.IS_PRODUCTION:
        batches = models.Batch.objects.filter(released__isnull=False)
    else:
        batches = models.Batch.objects.all()
    batches = batches.order_by('-released')
    paginator = Paginator(batches, 25)
    page = paginator.page(page_number)
    page_range_short = list(_page_range_short(paginator, page))

    return render_to_response('reports/batches.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
def batches_atom(request, page_number=1):
    batches = models.Batch.objects.filter(released__isnull=False)
    batches = batches.order_by('-released')
    now = rfc3339(datetime.datetime.now())

    paginator = Paginator(batches, 25)
    page = paginator.page(page_number)
    return render_to_response('reports/batches.xml', dictionary=locals(),
                              context_instance=RequestContext(request),
                              mimetype='application/atom+xml')


@cache_page(settings.API_TTL_SECONDS)
def batches_json(request, page_number=1):
    batches = models.Batch.objects.filter(released__isnull=False)
    batches = batches.order_by('-released')

    paginator = Paginator(batches, 25)
    page = paginator.page(page_number)
    b = [batch_to_json(b, serialize=False) for b in page.object_list]
    j = {'batches': b}

    host = "http://" + request.get_host()
    if page.has_next():
        j['next'] = host + urlresolvers.reverse('chronam_batches_json_page',
                args=[page.next_page_number()])

    if page.has_previous():
        j['previous'] = host + urlresolvers.reverse('chronam_batches_json_page',
                args=[page.previous_page_number()])

    return HttpResponse(json.dumps(j, indent=2), mimetype='application/json')


@cache_page(settings.API_TTL_SECONDS)
def batch(request, batch_name):
    batch = get_object_or_404(models.Batch, name=batch_name)
    reels = []
    for reel in batch.reels.all():
        reels.append({'number': reel.number,
                      'titles': reel.titles(),
                      'title_range': _title_range(reel),
                      'page_count': reel.pages.all().count(), })
    page_title = 'Batch: %s' % batch.name
    profile_uri = 'http://www.openarchives.org/ore/html/'

    # maybe when we can prefetch_related when django v1.4 is available
    # https://docs.djangoproject.com/en/dev/ref/models/querysets/#prefetch-related
    # this can be done more elegantly with the django ORM
    # for now it's ugly raw-sql and ugly indexed values in the template
    sql = """
          SELECT core_title.name,
              core_title.lccn,
              DATE_FORMAT(core_issue.date_issued, '%%Y-%%m-%%d') AS issued,
              COUNT(core_page.id) AS page_count,
              core_title.name_normal
          FROM core_batch, core_issue, core_title, core_page
          WHERE core_batch.name = %s
            AND core_issue.batch_id = core_batch.name
            AND core_issue.title_id = core_title.lccn
            AND core_page.issue_id = core_issue.id
          GROUP BY core_title.name,
              core_title.name_normal,
              core_title.lccn,
              issued
          ORDER BY core_title.name_normal, core_issue.date_issued ASC
          """
    cursor = connection.cursor()
    cursor.execute(sql, [batch.name])
    issue_stats = cursor.fetchall()

    return render_to_response('reports/batch.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
@rdf_view
def batch_rdf(request, batch_name):
    batch = get_object_or_404(models.Batch, name=batch_name)
    graph = batch_to_graph(batch)
    response = HttpResponse(graph.serialize(base=_rdf_base(request),
                                            include_base=True),
                            mimetype='application/rdf+xml')
    return response


@cache_page(settings.API_TTL_SECONDS)
def batch_json(request, batch_name):
    batch = get_object_or_404(models.Batch, name=batch_name)
    return HttpResponse(batch_to_json(batch), mimetype='application/json')


@cache_page(settings.API_TTL_SECONDS)
def event(request, event_id):
    page_title = 'Event'
    event = get_object_or_404(models.LoadBatchEvent, id=event_id)
    return render_to_response('reports/event.html', dictionary=locals(),
                             context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
def events(request, page_number=1):
    page_title = 'Events'
    events = models.LoadBatchEvent.objects.all().order_by('-created')
    paginator = Paginator(events, 25)
    page = paginator.page(page_number)
    page_range_short = list(_page_range_short(paginator, page))

    return render_to_response('reports/events.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
def events_atom(request, page_number=1):
    events = models.LoadBatchEvent.objects.all().order_by('-created')
    paginator = Paginator(events, 25)
    page = paginator.page(page_number)
    page_range_short = list(_page_range_short(paginator, page))
    return render_to_response('reports/events.xml', dictionary=locals(),
                              context_instance=RequestContext(request),
                              mimetype='application/atom+xml')


@cache_page(settings.DEFAULT_TTL_SECONDS)
def states(request, format='html'):
    page_title = 'States'
    # custom SQL to eliminate spelling errors and the like in cataloging data
    # TODO: maybe use Django ORM once the data is cleaned more on import
    cursor = connection.cursor()
    cursor.execute(
"SELECT state, COUNT(*) AS count FROM core_place \
WHERE state IS NOT NULL GROUP BY state HAVING count > 10 ORDER BY state")
    if format == 'json' or request.META['HTTP_ACCEPT'] == 'application/json':
        states = [n[0] for n in cursor.fetchall()]
        states.extend(["----------------", "American Samoa",
                       "Mariana Islands", "Puerto Rico", "Virgin Islands"])
        return HttpResponse(json.dumps(states),
                            mimetype='application/json')
    states = [n[0] for n in cursor.fetchall()]
    return render_to_response('reports/states.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.DEFAULT_TTL_SECONDS)
def counties_in_state(request, state, format='html'):
    state = unpack_url_path(state)
    if state is None:
        raise Http404
    page_title = 'Counties in %s' % state

    places = models.Place.objects.filter(state__iexact=state,
                                         county__isnull=False).all()
    county_names = sorted(set(p.county for p in places))

    if format == 'json':
        return HttpResponse(json.dumps(county_names),
                            mimetype='application/json')
    counties = [name for name in county_names]
    if len(counties) == 0:
        raise Http404
    return render_to_response('reports/counties.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.DEFAULT_TTL_SECONDS)
def states_counties(request, format='html'):
    page_title = 'Counties by State'

    cursor = connection.cursor()

    cursor.execute("\
SELECT state, county, COUNT(*) AS total FROM core_place \
WHERE state IS NOT NULL AND county IS NOT NULL \
GROUP BY state, county HAVING total >= 1 ORDER BY state, county")

    states_counties = [(n[0], n[1], n[2]) for n in cursor.fetchall()]

    return render_to_response('reports/states_counties.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.DEFAULT_TTL_SECONDS)
def cities_in_county(request, state, county, format='html'):
    state, county = map(unpack_url_path, (state, county))
    if state is None or county is None:
        raise Http404
    page_title = 'Cities in %s, %s' % (state, county)
    places = models.Place.objects.filter(state__iexact=state,
                                         county__iexact=county).all()
    cities = [p.city for p in places]
    if None in cities:
        cities.remove(None)
    if len(cities) == 0:
        raise Http404
    if format == 'json':
        return HttpResponse(json.dumps(cities),
                            mimetype='application/json')
    return render_to_response('reports/cities.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.DEFAULT_TTL_SECONDS)
def cities_in_state(request, state, format='html'):
    state = unpack_url_path(state)
    if state is None:
        raise Http404
    page_title = 'Cities in %s' % state

    places = models.Place.objects.filter(state__iexact=state,
                                         city__isnull=False).all()
    cities = sorted(set(p.city for p in places))

    if len(cities) == 0:
        raise Http404
    if format == 'json':
        return HttpResponse(json.dumps(cities),
                            mimetype='application/json')
    return render_to_response('reports/cities.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
def institutions(request, page_number=1):
    page_title = 'Institutions'
    institutions = models.Institution.objects.all()
    paginator = Paginator(institutions, 50)
    try:
        page = paginator.page(page_number)
    except InvalidPage:
        page = paginator.page(1)
    page_range_short = list(_page_range_short(paginator, page))
    return render_to_response('reports/institutions.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
def institution(request, code):
    institution = get_object_or_404(models.Institution, code=code)
    page_title = institution
    titles_count = models.Title.objects.filter(
        holdings__institution=institution).distinct().count()
    holdings_count = models.Holding.objects.filter(
        institution=institution).count()
    return render_to_response('reports/institution.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
def institution_titles(request, code, page_number=1):
    institution = get_object_or_404(models.Institution, code=code)
    page_title = 'Titles held by %s' % institution
    titles = models.Title.objects.filter(
        holdings__institution=institution).distinct()
    paginator = Paginator(titles, 50)
    try:
        page = paginator.page(page_number)
    except InvalidPage:
        page = paginator.page(1)
    page_range_short = list(_page_range_short(paginator, page))
    return render_to_response('reports/institution_titles.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(10)
def status(request):
    page_title = 'System Status'
    page_count = models.Page.objects.all().count()
    issue_count = models.Issue.objects.all().count()
    batch_count = models.Batch.objects.all().count()
    title_count = models.Title.objects.all().count()
    holding_count = models.Holding.objects.all().count()
    essay_count = models.Essay.objects.all().count()
    pages_indexed = index.page_count()
    titles_indexed = index.title_count()
    return render_to_response('reports/status.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
def awardees(request):
    page_title = 'Awardees'
    awardees = models.Awardee.objects.all().order_by('name')
    return render_to_response('reports/awardees.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
def awardees_json(request):
    awardees = []
    for awardee in models.Awardee.objects.all().order_by('name'):
        awardees.append(
            {
                'url': awardee.url,
                'name': awardee.name,
                'batch_count': awardee.batch_count,
                'page_count': awardee.page_count
            }
        )
    return HttpResponse(json.dumps(awardees, indent=2),
                        mimetype='application/json')


@cache_page(settings.API_TTL_SECONDS)
def awardee(request, institution_code):
    awardee = get_object_or_404(models.Awardee, org_code=institution_code)
    page_title = 'Awardee: %s' % awardee.name
    batches = models.Batch.objects.filter(awardee=awardee)
    return render_to_response('reports/awardee.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
@rdf_view
def awardee_rdf(request, institution_code):
    awardee = get_object_or_404(models.Awardee, org_code=institution_code)
    graph = awardee_to_graph(awardee)
    response = HttpResponse(graph.serialize(base=_rdf_base(request),
                                            include_base=True),
                            mimetype='application/rdf+xml')
    return response


@cache_page(settings.DEFAULT_TTL_SECONDS)
def terms(request):
    return render_to_response('reports/terms.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
def pages_on_flickr(request):
    page_title = "Flickr Report"
    flickr_urls = models.FlickrUrl.objects.all().order_by('-created')
    if len(flickr_urls) > 0:
        last_update = flickr_urls[0].created
    else:
        last_update = None
    return render_to_response('reports/pages_on_flickr.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.DEFAULT_TTL_SECONDS)
def batch_summary(request, format='html'):
    page_title = "Batch Summary"
    cursor = connection.cursor()
    cursor.execute("\
select batches.name, issues.title_id, min(date_issued), \
max(date_issued), count(pages.id) \
from batches, issues, pages \
where batches.name=issues.batch_id and issues.id=pages.issue_id \
group by batches.name, issues.title_id order by batches.name;")
    batch_details = cursor.fetchall()
    if format == 'txt':
        return render_to_response('batch_summary.txt', dictionary=locals(),
                                  context_instance=RequestContext(request),
                                  mimetype="text/plain")
    return render_to_response('batch_summary.html',
                              dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
def reels(request, page_number=1):
    page_title = 'Reels'
    reels = models.Reel.objects.all().order_by('number')
    paginator = Paginator(reels, 25)
    page = paginator.page(page_number)
    page_range_short = list(_page_range_short(paginator, page))

    return render_to_response('reports/reels.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
def reel(request, reel_number):
    crumbs = [
        {'label':'Reels',
         'href': urlresolvers.reverse('chronam_reels')},
        ]
    page_title = 'Reel %s' % reel_number
    m_reels = models.Reel.objects.filter(number=reel_number)
    reels = []
    for reel in m_reels:
        reels.append({'batch': reel.batch,
                      'titles': reel.titles(),
                      'title_range': _title_range(reel), })
    return render_to_response('reports/reel.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
def essays(request):
    page_title = "Newspaper Essays"
    essays = models.Essay.objects.all().order_by('title')
    return render_to_response('reports/essays.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
def essay(request, essay_id):
    essay = get_object_or_404(models.Essay, id=essay_id)
    title = essay.first_title()
    page_title = essay.title
    return render_to_response('reports/essay.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
def ocr_dumps_atom(request, page_number=1):
    batches = models.Batch.objects.filter(released__isnull=False)
    batches = batches.order_by('-released')
    now = rfc3339(datetime.datetime.now())

    paginator = Paginator(batches, 25)
    page = paginator.page(page_number)

    dumpfiles = []
    for filename in os.listdir(settings.OCR_DUMP_STORAGE):
        if re.match("^part-\d+.tar.bz2$", filename):
            # use file modified time to indicate when the dump was last modified
            full_path = os.path.join(settings.OCR_DUMP_STORAGE, filename)
            t = os.path.getmtime(full_path)
            updated = datetime.datetime.fromtimestamp(t)
            dumpfiles.append({"name": filename, "updated": updated})

    return render_to_response('reports/ocr_dumps.xml', dictionary=locals(),
                              context_instance=RequestContext(request),
                              mimetype='application/atom+xml')


@cache_page(settings.API_TTL_SECONDS)
def languages(request):
    page_title = 'Languages'
    languages = models.LanguageText.objects.values('language__code', 'language__name').annotate(
        count=Count('language'))

    return render_to_response('reports/languages.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
def language_batches(request, language, page_number=1):
    language_name = models.Language.objects.get(code=language).name
    page_title = 'Batches with %s text' % (language_name)
    batches = models.LanguageText.objects.filter(language__code=language).values('ocr__page__issue__batch').annotate(count=Count('ocr__page__issue__batch'))
    paginator = Paginator(batches, 25)
    try:
        page = paginator.page(page_number)
    except InvalidPage:
        page = paginator.page(1)
    page_range_short = list(_page_range_short(paginator, page))
    return render_to_response('reports/language_batches.html', dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.API_TTL_SECONDS)
def language_titles(request, language, page_number=1):
    language_name = models.Language.objects.get(code=language).name
    page_title = 'Titles with %s text' % (language_name)
    titles = models.LanguageText.objects.filter(language__code=language).values('ocr__page__issue__title').annotate(count=Count('ocr__page__issue__title'))
    paginator = Paginator(titles, 25)
    try:
        page = paginator.page(page_number)
    except InvalidPage:
        page = paginator.page(1)
    page_range_short = list(_page_range_short(paginator, page))
    return render_to_response('reports/language_titles.html', dictionary=locals(),
                              context_instance=RequestContext(request))


def _title_range(reel):
    agg = models.Issue.objects.filter(pages__reel=reel).distinct().aggregate(
            mn=Min('date_issued'), mx=Max('date_issued'))
    if agg['mn'] and agg['mx']:
        mn = datetime_safe.new_datetime(agg['mn']).strftime('%b %d, %Y')
        mx = datetime_safe.new_datetime(agg['mx']).strftime('%b %d, %Y')
        return "%s - %s" % (mn, mx)
    else:
        return ""
