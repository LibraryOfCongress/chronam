import csv
import datetime
import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Max, Min, Q
from django.http import Http404, HttpResponse, HttpResponseServerError
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.encoding import smart_str
from rfc3339 import rfc3339

from chronam.core import index, models
from chronam.core.decorator import add_cache_headers, cors, opensearch_clean
from chronam.core.rdf import titles_to_graph
from chronam.core.utils.url import unpack_url_path
from chronam.core.utils.utils import _page_range_short, _rdf_base, is_valid_jsonp_callback


@add_cache_headers(settings.METADATA_TTL_SECONDS)
def newspapers(request, state=None, format="html"):
    if state and state != "all_states":
        state = unpack_url_path(state)
        if state is None:
            raise Http404
        else:
            state = state.title()
    else:
        state = request.GET.get("state")

    language = language_display = None
    language_code = request.GET.get("language")
    if language_code:
        language = models.Language.objects.filter(code__startswith=language_code).first()
        if not language:
            language_code = None
        else:
            language_code = language.code
            language_display = language.name
    ethnicity = request.GET.get("ethnicity")

    if not state and not language and not ethnicity:
        page_title = "All Digitized Newspapers"
    else:
        page_title = "Results: Digitized Newspapers"

    titles = models.Title.objects.filter(has_issues=True)
    titles = titles.annotate(first=Min("issues__date_issued"))
    titles = titles.annotate(last=Max("issues__date_issued"))

    if state:
        titles = titles.filter(places__state__iexact=state)

    if language:
        titles = titles.filter(languages=language)

    if ethnicity:
        try:
            e = models.Ethnicity.objects.get(name=ethnicity)
            ethnicity_filter = Q(subjects__heading__icontains=ethnicity)
            for s in e.synonyms.all():
                ethnicity_filter |= Q(subjects__heading__icontains=s.synonym)
            titles = titles.filter(ethnicity_filter)
        except models.Ethnicity.DoesNotExist:
            pass

    _newspapers_by_state = {}
    for title in titles.prefetch_related("places"):
        if state:
            _newspapers_by_state.setdefault(state, set()).add(title)
        else:
            for place in title.places.all():
                if place.state:
                    _newspapers_by_state.setdefault(place.state, set()).add(title)

    newspapers_by_state = [
        (s, sorted(t, key=lambda title: title.name_normal))
        for s, t in sorted(_newspapers_by_state.iteritems())
    ]
    crumbs = list(settings.BASE_CRUMBS)

    if format == "html":
        return render_to_response(
            "newspapers.html", dictionary=locals(), context_instance=RequestContext(request)
        )
    elif format == "txt":
        host = request.get_host()
        return render_to_response(
            "newspapers.txt",
            dictionary=locals(),
            context_instance=RequestContext(request),
            content_type="text/plain",
        )
    elif format == "csv":
        csv_header_labels = (
            "Persistent Link",
            "State",
            "Title",
            "LCCN",
            "OCLC",
            "ISSN",
            "No. of Issues",
            "First Issue Date",
            "Last Issue Date",
            "More Info",
        )
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="chronam_newspapers.csv"'
        writer = csv.writer(response)
        writer.writerow(csv_header_labels)
        for state, titles in newspapers_by_state:
            for title in titles:
                writer.writerow(
                    (
                        request.build_absolute_uri(reverse("chronam_issues", kwargs={"lccn": title.lccn})),
                        state,
                        title,
                        title.lccn or "",
                        title.oclc or "",
                        title.issn or "",
                        title.issues.count(),
                        title.first,
                        title.last,
                        request.build_absolute_uri(
                            reverse("chronam_title_essays", kwargs={"lccn": title.lccn})
                        ),
                    )
                )
        return response

    elif format == "json":
        results = {"newspapers": []}
        for state, titles in newspapers_by_state:
            for title in titles:
                results["newspapers"].append(
                    {
                        "lccn": title.lccn,
                        "title": title.display_name,
                        "url": request.build_absolute_uri(title.json_url),
                        "state": state,
                    }
                )

        return HttpResponse(json.dumps(results), content_type="application/json")
    else:
        return HttpResponseServerError("unsupported format: %s" % format)


@cors
@add_cache_headers(settings.DEFAULT_TTL_SECONDS)
@opensearch_clean
def search_titles_results(request):
    page_title = "US Newspaper Directory Search Results"
    crumbs = list(settings.BASE_CRUMBS)
    crumbs.extend([{"label": "Search Newspaper Directory", "href": reverse("chronam_search_titles")}])

    def prep_title_for_return(t):
        title = {}
        title.update(t.solr_doc)
        title["oclc"] = t.oclc
        return title

    format = request.GET.get("format")

    # check if requested format is CSV before building pages for response. CSV
    # response does not make use of pagination, instead all matching titles from
    # SOLR are returned at once
    if format == "csv":
        query = request.GET.copy()
        q, fields, sort_field, sort_order = index.get_solr_request_params_from_query(query)

        # return all titles in csv format. * May hurt performance. Assumption is that this
        # request is not made often.
        # TODO: revisit if assumption is incorrect
        solr_response = index.execute_solr_query(q, fields, sort_field, sort_order, index.title_count(), 0)
        titles = index.get_titles_from_solr_documents(solr_response)

        csv_header_labels = (
            "lccn",
            "title",
            "place_of_publication",
            "start_year",
            "end_year",
            "publisher",
            "edition",
            "frequency",
            "subject",
            "state",
            "city",
            "country",
            "language",
            "oclc",
            "holding_type",
        )
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="chronam_titles.csv"'
        writer = csv.writer(response)
        writer.writerow(csv_header_labels)
        for title in titles:
            writer.writerow(
                map(
                    lambda val: smart_str(val or "--"),
                    (
                        title.lccn,
                        title.name,
                        title.place_of_publication,
                        title.start_year,
                        title.end_year,
                        title.publisher,
                        title.edition,
                        title.frequency,
                        map(str, title.subjects.all()),
                        set(map(lambda p: p.state, title.places.all())),
                        map(lambda p: p.city, title.places.all()),
                        str(title.country),
                        map(str, title.languages.all()),
                        title.oclc,
                        title.holding_types,
                    ),
                )
            )
        return response

    try:
        curr_page = int(request.GET.get("page", 1))
    except ValueError as e:
        curr_page = 1

    paginator = index.SolrTitlesPaginator(request.GET)

    try:
        page = paginator.page(curr_page)
    except:
        raise Http404

    page_range_short = list(_page_range_short(paginator, page))

    try:
        rows = int(request.GET.get("rows", "20"))
    except ValueError as e:
        rows = 20

    query = request.GET.copy()
    query.rows = rows
    if page.has_next():
        query["page"] = curr_page + 1
        next_url = "?" + query.urlencode()
    if page.has_previous():
        query["page"] = curr_page - 1
        previous_url = "?" + query.urlencode()
    start = page.start_index()
    end = page.end_index()
    host = request.get_host()
    page_list = []
    for p in range(len(page.object_list)):
        page_start = start + p
        page_list.append((page_start, page.object_list[p]))

    if format == "atom":
        feed_url = request.build_absolute_uri()
        updated = rfc3339(datetime.datetime.now())
        return render_to_response(
            "search_titles_results.xml",
            dictionary=locals(),
            context_instance=RequestContext(request),
            content_type="application/atom+xml",
        )

    elif format == "json":
        results = {
            "startIndex": start,
            "endIndex": end,
            "totalItems": paginator.count,
            "itemsPerPage": rows,
            "items": [prep_title_for_return(t) for t in page.object_list],
        }
        # add url for the json view
        for i in results["items"]:
            i["url"] = request.build_absolute_uri(i["id"].rstrip("/") + ".json")
        json_text = json.dumps(results)
        # jsonp?
        callback = request.GET.get("callback")
        if callback and is_valid_jsonp_callback(callback):
            json_text = "%s(%s);" % ("callback", json_text)
        return HttpResponse(json_text, content_type="application/json")

    sort = request.GET.get("sort", "relevance")

    q = request.GET.copy()
    if "page" in q:
        del q["page"]
    if "sort" in q:
        del q["sort"]
    q = q.urlencode()
    collapse_search_tab = True
    return render_to_response(
        "search_titles_results.html", dictionary=locals(), context_instance=RequestContext(request)
    )


@add_cache_headers(settings.DEFAULT_TTL_SECONDS)
def newspapers_rdf(request):
    titles = models.Title.objects.filter(has_issues=True)
    titles = titles.prefetch_related(
        "subjects",
        "languages",
        "essays",
        "places",
        "urls",
        "succeeding_title_links",
        "preceeding_title_links",
        "related_title_links",
    )
    titles = titles.select_related("marc")

    graph = titles_to_graph(titles)
    return HttpResponse(
        graph.serialize(base=_rdf_base(request), include_base=True), content_type="application/rdf+xml"
    )
