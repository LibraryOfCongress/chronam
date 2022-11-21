import datetime
import json
import logging
import re

from django.conf import settings
from django.core import urlresolvers
from django.core.paginator import EmptyPage, InvalidPage
from django.db.models import Q
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import render_to_response
from django.template import RequestContext
from rfc3339 import rfc3339

from chronam.core import forms, index, models
from chronam.core.decorator import add_cache_headers, cors, opensearch_clean, robots_tag
from chronam.core.utils.utils import _page_range_short, is_valid_jsonp_callback


def search_pages_paginator(request):
    # front page only
    try:
        sequence = int(request.GET.get("sequence", "0"))
    except ValueError:
        sequence = 0
    # set results per page value
    try:
        rows = int(request.GET.get("rows", "20"))
    except ValueError:
        rows = 20
    q = request.GET.copy()
    q["rows"] = rows
    q["sequence"] = sequence
    paginator = index.SolrPaginator(q)
    return paginator


@robots_tag
@cors
@add_cache_headers(settings.DEFAULT_TTL_SECONDS)
@opensearch_clean
def search_pages_results(request, view_type="gallery"):
    page_title = "Search Results"
    paginator = search_pages_paginator(request)
    q = paginator.query

    try:
        page = paginator.page(paginator._cur_page)
    except InvalidPage:
        url = urlresolvers.reverse("chronam_search_pages_results")
        # Set the page to the first page
        q["page"] = 1
        return HttpResponseRedirect("%s?%s" % (url, q.urlencode()))
    except Exception as exc:
        logging.exception(
            "Unable to paginate search results", extra={"data": {"q": q, "page": paginator._cur_page}}
        )

        if getattr(exc, "httpcode", None) == 400:
            return HttpResponseBadRequest()
        else:
            raise
    start = page.start_index()
    end = page.end_index()

    # figure out the next page number
    query = request.GET.copy()
    if page.has_next():
        query["page"] = paginator._cur_page + 1
        next_url = "?" + query.urlencode()
        # and the previous page number
    if page.has_previous():
        query["page"] = paginator._cur_page - 1
        previous_url = "?" + query.urlencode()

    rows = q["rows"] if "rows" in q else 20
    crumbs = list(settings.BASE_CRUMBS)

    host = request.get_host()
    response_format = request.GET.get("format")
    if response_format == "atom":
        feed_url = request.build_absolute_uri()
        updated = rfc3339(datetime.datetime.now())
        return render_to_response(
            "search_pages_results.xml",
            dictionary=locals(),
            context_instance=RequestContext(request),
            content_type="application/atom+xml",
        )
    elif response_format == "json":
        results = {
            "startIndex": start,
            "endIndex": end,
            "totalItems": paginator.count,
            "itemsPerPage": rows,
            "items": [p.solr_doc for p in page.object_list],
        }
        for i in results["items"]:
            i["url"] = request.build_absolute_uri(i["id"].rstrip("/") + ".json")
        json_text = json.dumps(results)
        # jsonp?
        callback = request.GET.get("callback")
        if callback and is_valid_jsonp_callback(callback):
            json_text = "%s(%s);" % (callback, json_text)
        return HttpResponse(json_text, content_type="application/json")
    page_range_short = list(_page_range_short(paginator, page))
    # copy the current request query without the page and sort
    # query params so we can construct links with it in the template
    q = request.GET.copy()
    for i in ("page", "sort"):
        if i in q:
            q.pop(i)
    q = q.urlencode()

    # get an pseudo english version of the query
    english_search = paginator.englishify()

    # get some stuff from the query string for use in the form
    lccns = query.getlist("lccn")
    states = query.getlist("state")

    # figure out the sort that's in use
    sort = query.get("sort", "relevance")
    if view_type == "list":
        template = "search_pages_results_list.html"
    else:
        template = "search_pages_results.html"
    page_list = []
    for count in range(len(page.object_list)):
        page_list.append((count + start, page.object_list[count]))
    return render_to_response(template, dictionary=locals(), context_instance=RequestContext(request))


@robots_tag
@add_cache_headers(settings.METADATA_TTL_SECONDS)
def search_titles(request):
    browse_val = [chr(n) for n in range(65, 91)]
    browse_val.extend([str(i) for i in range(10)])
    form = forms.SearchTitlesForm()
    title_count = models.Title.objects.all().count()
    page_name = "directory"
    page_title = "Search U.S. Newspaper Directory, 1690-Present"
    template = "news_directory.html"
    collapse_search_tab = True
    crumbs = list(settings.BASE_CRUMBS)
    return render_to_response(template, dictionary=locals(), context_instance=RequestContext(request))


@robots_tag
@add_cache_headers(settings.METADATA_TTL_SECONDS)
def search_titles_opensearch(request):
    host = request.get_host()
    return render_to_response(
        "search_titles_opensearch.xml",
        content_type="application/opensearchdescription+xml",
        dictionary=locals(),
        context_instance=RequestContext(request),
    )


@robots_tag
@add_cache_headers(settings.DEFAULT_TTL_SECONDS)
def search_pages_opensearch(request):
    host = request.get_host()
    return render_to_response(
        "search_pages_opensearch.xml",
        content_type="application/opensearchdescription+xml",
        dictionary=locals(),
        context_instance=RequestContext(request),
    )


@robots_tag
@cors
@add_cache_headers(settings.DEFAULT_TTL_SECONDS)
def suggest_titles(request):
    q = request.GET.get("q", "")
    q = q.lower()

    # remove initial articles (maybe there are more?)
    q = re.sub(r"^(the|a|an) ", "", q)

    # build up the suggestions
    # See http://www.opensearch.org/Specifications/OpenSearch/Extensions/Suggestions/1.0
    # for details on why the json is this way

    titles = []
    descriptions = []
    urls = []

    lccn_q = Q(lccn__startswith=q)
    title_q = Q(name_normal__startswith=q)
    for t in models.Title.objects.filter(lccn_q | title_q)[0:50]:
        titles.append(str(t))
        descriptions.append(t.lccn)
        urls.append(request.build_absolute_uri(t.url))

    suggestions = [q, titles, descriptions, urls]
    json_text = json.dumps(suggestions)
    callback = request.GET.get("callback")
    if callback and is_valid_jsonp_callback(callback):
        json_text = "%s(%s);" % (callback, json_text)
    return HttpResponse(json_text, content_type="application/x-suggestions+json")


@robots_tag
@add_cache_headers(settings.DEFAULT_TTL_SECONDS)
def search_pages_navigation(request):
    """Search results navigation data

    This view provides the information needed to add search result
    navigation to a page.

    """
    if not ("page" in request.GET and "index" in request.GET):
        return HttpResponseNotFound()

    search_url = urlresolvers.reverse("chronam_search_pages_results")

    try:
        paginator = search_pages_paginator(request)
    except (EmptyPage, InvalidPage):
        return HttpResponseBadRequest()

    search = {}
    search["total"] = paginator.count
    search["current"] = paginator.overall_index + 1  # current is 1-based
    search["results"] = search_url + "?" + paginator.query.urlencode()

    try:
        search["previous_result"] = paginator.previous_result
        search["next_result"] = paginator.next_result
    except EmptyPage:
        pass

    return JsonResponse(search)


@robots_tag
@add_cache_headers(settings.DEFAULT_TTL_SECONDS)
def search_advanced(request):
    adv_search_form = forms.AdvSearchPagesForm()
    template = "search_advanced.html"
    crumbs = list(settings.BASE_CRUMBS)
    page_title = "Advanced Search"
    return render_to_response(template, dictionary=locals(), context_instance=RequestContext(request))
