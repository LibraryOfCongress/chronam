import datetime
import json

from django.conf import settings
from django.core.paginator import InvalidPage, Paginator
from django.core.urlresolvers import reverse
from django.db import connection
from django.db.models import Count, Max, Min
from django.http import Http404, HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils import datetime_safe
from django.views.decorators.cache import never_cache
from rfc3339 import rfc3339
from tabular_export.core import export_to_csv_response, flatten_queryset

from chronam.core import index, models
from chronam.core.decorator import add_cache_headers, cors
from chronam.core.rdf import awardee_to_graph, batch_to_graph
from chronam.core.utils.url import unpack_url_path
from chronam.core.utils.utils import _get_tip, _page_range_short, _rdf_base


@add_cache_headers(settings.METADATA_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def total_page_count(request):
    return JsonResponse({"total_page_count": index.page_count()})


@add_cache_headers(settings.LONG_TTL_SECONDS)
def reports(request):
    page_title = "Reports"
    return render_to_response(
        "reports/reports.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@never_cache
def batches(request, page_number=1):
    page_title = "Batches"
    batches = models.Batch.viewable_batches()
    batches = batches.prefetch_related("awardee")
    paginator = Paginator(batches, 25)
    page = paginator.page(page_number)
    page_range_short = list(_page_range_short(paginator, page))

    return render_to_response(
        "reports/batches.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@never_cache
def batches_atom(request, page_number=1):
    batches = models.Batch.viewable_batches()
    batches = batches.order_by("-released")
    now = rfc3339(datetime.datetime.now())

    paginator = Paginator(batches, 25)
    page = paginator.page(page_number)
    return render_to_response(
        "reports/batches.xml",
        dictionary=locals(),
        context_instance=RequestContext(request),
        content_type="application/atom+xml",
    )


@cors
@never_cache
def batches_json(request, page_number=1):
    viewable_batches = models.Batch.viewable_batches()
    paginator = Paginator(viewable_batches, 25)
    page = paginator.page(page_number)
    batches = [batch.json(request, serialize=False, include_issues=False) for batch in page.object_list]
    payload = {"batches": batches}

    if page.has_next():
        url_next = reverse("chronam_batches_json_page", args=[page.next_page_number()])
        payload["next"] = request.build_absolute_uri(url_next)

    if page.has_previous():
        url_prev = reverse("chronam_batches_json_page", args=[page.previous_page_number()])
        payload["previous"] = request.build_absolute_uri(url_prev)

    return JsonResponse(payload)


@never_cache
def batches_csv(request):
    qs = models.Batch.viewable_batches()
    qs = qs.annotate(page_count=Count("issues__pages"))
    headers, data = flatten_queryset(
        qs,
        field_names=["created", "name", "awardee__name", "page_count", "released"],
        extra_verbose_names={"awardee__name": "Awardee"},
    )

    return export_to_csv_response("chronam_batches.csv", headers, data)


@never_cache
def batch(request, batch_name):
    batch = get_object_or_404(models.Batch, name=batch_name)
    reels = []
    for reel in batch.reels.all():
        reels.append(
            {
                "number": reel.number,
                "titles": reel.titles(),
                "title_range": _title_range(reel),
                "page_count": reel.pages.all().count(),
            }
        )
    page_title = "Batch: %s" % batch.name

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
              core_issue.date_issued
          ORDER BY core_title.name_normal ASC, core_issue.date_issued ASC
          """
    cursor = connection.cursor()
    cursor.execute(sql, [batch.name])
    issue_stats = cursor.fetchall()

    return render_to_response(
        "reports/batch.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@never_cache
def batch_rdf(request, batch_name):
    batch = get_object_or_404(models.Batch, name=batch_name)
    graph = batch_to_graph(batch)
    response = HttpResponse(
        graph.serialize(base=_rdf_base(request), include_base=True), content_type="application/rdf+xml"
    )
    return response


@cors
@never_cache
def batch_json(request, batch_name):
    batch = get_object_or_404(models.Batch, name=batch_name)
    return HttpResponse(batch.json(request), content_type="application/json")


@cors
@add_cache_headers(settings.API_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def title_json(request, lccn):
    title = get_object_or_404(models.Title, lccn=lccn)
    return HttpResponse(title.json(request), content_type="application/json")


@cors
@add_cache_headers(settings.API_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def issue_pages_json(request, lccn, date, edition):
    title, issue, page = _get_tip(lccn, date, edition)
    if issue:
        return HttpResponse(issue.json(request), content_type="application/json")
    else:
        return HttpResponseNotFound()


@cors
@add_cache_headers(settings.API_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def page_json(request, lccn, date, edition, sequence):
    title, issue, page = _get_tip(lccn, date, edition, sequence)
    if page:
        return HttpResponse(page.json(request), content_type="application/json")
    else:
        return HttpResponseNotFound()


@never_cache
def events(request, page_number=1):
    page_title = "Events"
    events = models.LoadBatchEvent.objects.all().order_by("-created")
    paginator = Paginator(events, 25)
    page = paginator.page(page_number)
    page_range_short = list(_page_range_short(paginator, page))

    return render_to_response(
        "reports/events.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@never_cache
def events_csv(request):
    headers, data = flatten_queryset(
        models.LoadBatchEvent.objects.all().order_by("-created"),
        field_names=["created", "batch_name", "message"],
        extra_verbose_names={"created": "Time", "batch_name": "Batch name"},
    )
    return export_to_csv_response("chronam_events.csv", headers, data)


@never_cache
def events_atom(request, page_number=1):
    events = models.LoadBatchEvent.objects.all().order_by("-created")
    paginator = Paginator(events, 25)
    page = paginator.page(page_number)
    page_range_short = list(_page_range_short(paginator, page))
    return render_to_response(
        "reports/events.xml",
        dictionary=locals(),
        context_instance=RequestContext(request),
        content_type="application/atom+xml",
    )


@add_cache_headers(settings.LONG_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def states(request, format="html"):
    page_title = "States"
    # custom SQL to eliminate spelling errors and the like in cataloging data
    # TODO: maybe use Django ORM once the data is cleaned more on import
    cursor = connection.cursor()
    non_states = ("----------------", "American Samoa", "Mariana Islands", "Puerto Rico", "Virgin Islands")
    sql = (
        "SELECT state, COUNT(*) AS count FROM core_place",
        "WHERE state IS NOT NULL",
        "AND state NOT IN %s" % (non_states,),
        "GROUP BY state HAVING count > 10",
        "ORDER BY state",
    )
    cursor.execute(" ".join(sql))
    if format == "json" or request.META["HTTP_ACCEPT"] == "application/json":
        states = [n[0] for n in cursor.fetchall()]
        states.extend(non_states)
        return HttpResponse(json.dumps(states), content_type="application/json")
    states = [n[0] for n in cursor.fetchall()]
    return render_to_response(
        "reports/states.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@add_cache_headers(settings.DEFAULT_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def counties_in_state(request, state, format="html"):
    state = unpack_url_path(state)
    if state is None:
        raise Http404
    page_title = "Counties in %s" % state

    places = models.Place.objects.filter(state__iexact=state, county__isnull=False).all()
    county_names = sorted(set(p.county for p in places))

    if format == "json":
        return HttpResponse(json.dumps(county_names), content_type="application/json")
    counties = [name for name in county_names]
    if len(counties) == 0:
        raise Http404
    return render_to_response(
        "reports/counties.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@add_cache_headers(settings.LONG_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def states_counties(request, format="html"):
    page_title = "Counties by State"

    cursor = connection.cursor()

    cursor.execute(
        "\
SELECT state, county, COUNT(*) AS total FROM core_place \
WHERE state IS NOT NULL AND county IS NOT NULL \
GROUP BY state, county HAVING total >= 1 ORDER BY state, county"
    )

    states_counties = [(n[0], n[1], n[2]) for n in cursor.fetchall()]

    return render_to_response(
        "reports/states_counties.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@add_cache_headers(settings.LONG_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def cities_in_county(request, state, county, format="html"):
    state, county = map(unpack_url_path, (state, county))
    if state is None or county is None:
        raise Http404
    page_title = "Cities in %s, %s" % (state, county)
    places = models.Place.objects.filter(state__iexact=state, county__iexact=county).all()
    cities = [p.city for p in places]
    if None in cities:
        cities.remove(None)
    if len(cities) == 0:
        raise Http404
    if format == "json":
        return HttpResponse(json.dumps(cities), content_type="application/json")
    return render_to_response(
        "reports/cities.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@add_cache_headers(settings.LONG_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def cities_in_state(request, state, format="html"):
    state = unpack_url_path(state)
    if state is None:
        raise Http404
    page_title = "Cities in %s" % state

    places = models.Place.objects.filter(state__iexact=state, city__isnull=False).all()
    cities = sorted(set(p.city for p in places))

    if len(cities) == 0:
        raise Http404
    if format == "json":
        return HttpResponse(json.dumps(cities), content_type="application/json")
    return render_to_response(
        "reports/cities.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@add_cache_headers(settings.LONG_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def institutions(request, page_number=1):
    page_title = "Institutions"
    institutions = models.Institution.objects.all()
    paginator = Paginator(institutions, 50)
    try:
        page = paginator.page(page_number)
    except InvalidPage:
        page = paginator.page(1)
    page_range_short = list(_page_range_short(paginator, page))
    return render_to_response(
        "reports/institutions.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@add_cache_headers(settings.LONG_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def institution(request, code):
    institution = get_object_or_404(models.Institution, code=code)
    page_title = institution
    titles_count = models.Title.objects.filter(holdings__institution=institution).distinct().count()
    holdings_count = models.Holding.objects.filter(institution=institution).count()
    return render_to_response(
        "reports/institution.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@add_cache_headers(settings.LONG_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def institution_titles(request, code, page_number=1):
    institution = get_object_or_404(models.Institution, code=code)
    page_title = "Titles held by %s" % institution
    titles = models.Title.objects.filter(holdings__institution=institution).distinct()
    paginator = Paginator(titles, 50)
    try:
        page = paginator.page(page_number)
    except InvalidPage:
        page = paginator.page(1)
    page_range_short = list(_page_range_short(paginator, page))
    return render_to_response(
        "reports/institution_titles.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@never_cache
def status(request):
    page_title = "System Status"
    page_count = models.Page.objects.all().count()
    issue_count = models.Issue.objects.all().count()
    batch_count = models.Batch.objects.all().count()
    title_count = models.Title.objects.all().count()
    holding_count = models.Holding.objects.all().count()
    essay_count = models.Essay.objects.all().count()
    pages_indexed = index.page_count()
    titles_indexed = index.title_count()
    return render_to_response(
        "reports/status.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@add_cache_headers(settings.METADATA_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def awardees(request):
    page_title = "Awardees"
    awardees = models.Awardee.objects.all().order_by("name")
    return render_to_response(
        "reports/awardees.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@cors
@add_cache_headers(settings.METADATA_TTL_SECONDS)
def awardees_json(request):
    awardees = {"awardees": []}

    for awardee in models.Awardee.objects.all().order_by("name"):
        a = {"url": request.build_absolute_uri(awardee.json_url), "name": awardee.name}
        awardees["awardees"].append(a)

    return HttpResponse(json.dumps(awardees), content_type="application/json")


@add_cache_headers(settings.METADATA_TTL_SECONDS)
def awardee(request, institution_code):
    awardee = get_object_or_404(models.Awardee, org_code=institution_code)
    page_title = "Awardee: %s" % awardee.name
    batches = models.Batch.objects.filter(awardee=awardee)
    return render_to_response(
        "reports/awardee.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@cors
@add_cache_headers(settings.METADATA_TTL_SECONDS)
def awardee_json(request, institution_code):
    awardee = get_object_or_404(models.Awardee, org_code=institution_code)
    j = awardee.json(request, serialize=False)
    j["batches"] = []
    for batch in awardee.batches.all():
        j["batches"].append({"name": batch.name, "url": request.build_absolute_uri(batch.json_url)})
    return JsonResponse(j)


@add_cache_headers(settings.METADATA_TTL_SECONDS)
def awardee_rdf(request, institution_code):
    awardee = get_object_or_404(models.Awardee, org_code=institution_code)
    graph = awardee_to_graph(awardee)
    response = HttpResponse(
        graph.serialize(base=_rdf_base(request), include_base=True), content_type="application/rdf+xml"
    )
    return response


@add_cache_headers(settings.LONG_TTL_SECONDS)
def terms(request):
    return render_to_response(
        "reports/terms.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@add_cache_headers(settings.API_TTL_SECONDS)
def pages_on_flickr(request):
    page_title = "Flickr Report"
    flickr_urls = models.FlickrUrl.objects.all().order_by("-created")
    if len(flickr_urls) > 0:
        last_update = flickr_urls[0].created
    else:
        last_update = None
    return render_to_response(
        "reports/pages_on_flickr.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@add_cache_headers(settings.DEFAULT_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def batch_summary(request, format="html"):
    page_title = "Batch Summary"
    cursor = connection.cursor()
    sql = """
          select cb.name, ci.title_id, min(date_issued),
          max(date_issued), count(cp.id)
          from core_batch cb, core_issue ci, core_page cp
          where cb.name=ci.batch_id and ci.id=cp.issue_id
          group by cb.name, ci.title_id order by cb.name;
          """

    cursor = connection.cursor()
    cursor.execute(sql)
    batch_details = cursor.fetchall()
    if format == "txt":
        return render_to_response(
            "reports/batch_summary.txt",
            dictionary=locals(),
            context_instance=RequestContext(request),
            content_type="text/plain",
        )
    return render_to_response(
        "reports/batch_summary.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@add_cache_headers(settings.METADATA_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def reels(request, page_number=1):
    page_title = "Reels"
    reels = models.Reel.objects.all().order_by("number")
    paginator = Paginator(reels, 25)
    page = paginator.page(page_number)
    page_range_short = list(_page_range_short(paginator, page))

    return render_to_response(
        "reports/reels.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@add_cache_headers(settings.METADATA_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def reel(request, reel_number):
    crumbs = list(settings.BASE_CRUMBS)
    crumbs.extend([{"label": "Reels", "href": reverse("chronam_reels")}])
    page_title = "Reel %s" % reel_number
    m_reels = models.Reel.objects.filter(number=reel_number)
    reels = []
    for reel in m_reels:
        reels.append({"batch": reel.batch, "titles": reel.titles(), "title_range": _title_range(reel)})
    return render_to_response(
        "reports/reel.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@add_cache_headers(settings.METADATA_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def essays(request):
    page_title = "Newspaper Essays"
    essays = models.Essay.objects.all().order_by("title")
    return render_to_response(
        "reports/essays.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@add_cache_headers(settings.METADATA_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def essay(request, essay_id):
    essay = get_object_or_404(models.Essay, id=essay_id)
    title = essay.first_title()
    page_title = essay.title
    return render_to_response(
        "reports/essay.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@add_cache_headers(settings.METADATA_TTL_SECONDS, settings.SHARED_CACHE_MAXAGE_SECONDS)
def ocr(request):
    page_title = "OCR Data"
    dumps = models.OcrDump.objects.all().order_by("-created")
    return render_to_response(
        "reports/ocr.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@add_cache_headers(settings.METADATA_TTL_SECONDS)
def ocr_atom(request):
    dumps = models.OcrDump.objects.all().order_by("-created")
    if dumps.count() > 0:
        last_updated = dumps[0].created
    else:
        last_updated = datetime.datetime.now()
    return render_to_response(
        "reports/ocr.xml",
        dictionary=locals(),
        context_instance=RequestContext(request),
        content_type="application/atom+xml",
    )


@cors
@add_cache_headers(settings.METADATA_TTL_SECONDS)
def ocr_json(request):
    j = {"ocr": []}
    for dump in models.OcrDump.objects.all().order_by("-created"):
        j["ocr"].append(dump.json(request, serialize=False))
    return JsonResponse(j)


@never_cache
def languages(request):
    page_title = "Languages"
    languages = models.LanguageText.objects.values("language__code", "language__name").annotate(
        count=Count("language")
    )

    return render_to_response(
        "reports/languages.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@never_cache
def language_batches(request, language, page_number=1):
    language_name = models.Language.objects.get(code=language).name
    page_title = "Batches with %s text" % (language_name)
    if language != "eng":
        batches = (
            models.Batch.objects.filter(issues__pages__ocr__language_texts__language__code=language)
            .values("name")
            .annotate(count=Count("name"))
        )
        paginator = Paginator(batches, 25)
        try:
            page = paginator.page(page_number)
        except InvalidPage:
            page = paginator.page(1)
        page_range_short = list(_page_range_short(paginator, page))
    return render_to_response(
        "reports/language_batches.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@never_cache
def language_titles(request, language, page_number=1):
    language_name = models.Language.objects.get(code=language).name
    page_title = "Titles with %s text" % (language_name)
    if language != "eng":
        titles = (
            models.Title.objects.filter(issues__pages__ocr__language_texts__language__code=language)
            .values("lccn", "issues__batch__name")
            .annotate(count=Count("lccn"))
        )
        paginator = Paginator(titles, 25)
        try:
            page = paginator.page(page_number)
        except InvalidPage:
            page = paginator.page(1)
        page_range_short = list(_page_range_short(paginator, page))
    return render_to_response(
        "reports/language_titles.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@never_cache
def language_pages(request, language, batch, title=None, page_number=1):
    language_name = models.Language.objects.get(code=language).name
    page_title = "Pages with %s text" % (language_name)
    path = "reports/language_title_pages.html"
    if language != "eng":
        if title:
            pages = (
                models.Page.objects.filter(
                    ocr__language_texts__language__code=language, issue__title__lccn=title
                )
                .values(
                    "reel__number", "issue__date_issued", "issue__title__lccn", "issue__edition", "sequence"
                )
                .order_by("reel__number", "issue__date_issued", "sequence")
            )
        else:
            pages = (
                models.Page.objects.filter(
                    ocr__language_texts__language__code=language, issue__batch__name=batch
                )
                .values(
                    "reel__number", "issue__date_issued", "issue__title__lccn", "issue__edition", "sequence"
                )
                .order_by("reel__number", "issue__title__lccn", "issue__date_issued", "sequence")
            )
            path = "reports/language_batch_pages.html"
        paginator = Paginator(pages, 25)
        try:
            page = paginator.page(page_number)
        except InvalidPage:
            page = paginator.page(1)
        page_range_short = list(_page_range_short(paginator, page))
    return render_to_response(path, dictionary=locals(), context_instance=RequestContext(request))


def _title_range(reel):
    agg = (
        models.Issue.objects.filter(pages__reel=reel)
        .distinct()
        .aggregate(mn=Min("date_issued"), mx=Max("date_issued"))
    )
    if agg["mn"] and agg["mx"]:
        mn = datetime_safe.new_datetime(agg["mn"]).strftime("%b %d, %Y")
        mx = datetime_safe.new_datetime(agg["mx"]).strftime("%b %d, %Y")
        return "%s - %s" % (mn, mx)
    else:
        return ""
