import datetime
import json
from rfc3339 import rfc3339

from django.conf import settings
from django.core import urlresolvers
from django.db import connection
from django.http import Http404, HttpResponse
from django.db.models import Count, Max, Min, Q
from django.shortcuts import render_to_response
from django.template import RequestContext

from chronam.core.decorator import cache_page, opensearch_clean, rdf_view, cors
from chronam.core.utils.utils import _page_range_short, _rdf_base
from chronam.core import models, index
from chronam.core.rdf import titles_to_graph
from chronam.core.utils.url import unpack_url_path

@cache_page(settings.DEFAULT_TTL_SECONDS)
def newspapers(request, state=None, format='html'):
    if state and state != "all_states":        
        state = unpack_url_path(state)
        if state is None:
            raise Http404
    else:
        state = request.REQUEST.get('state', None)

    language = request.REQUEST.get('language', None)
    ethnicity = request.REQUEST.get('ethnicity', None)

    if not state and not language:
        page_title = 'All Digitized Newspapers'
    else:
        page_title = 'Results: Digitized Newspapers'
        number_of_pages = index.page_count()

    titles = models.Title.objects.filter(has_issues=True)
    titles = titles.annotate(first=Min('issues__date_issued'))
    titles = titles.annotate(last=Max('issues__date_issued'))

    if state:
        titles = titles.filter(places__state__iexact=state)

    if language:
        titles = titles.filter(languages__code__contains=language)

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
    for title in titles:
        if state:
            _newspapers_by_state.setdefault(state, set()).add(title)
        else:
            for place in title.places.all():
                if place.state:
                    _newspapers_by_state.setdefault(place.state, set()).add(title)

    newspapers_by_state = [(s, sorted(t)) for (s, t) in _newspapers_by_state.iteritems()]

    if format == "html":
        return render_to_response("newspapers.html",
                                  dictionary=locals(),
                                  context_instance=RequestContext(request))
    elif format == "txt":
        host = request.get_host()
        return render_to_response("newspapers.txt",
                                  dictionary=locals(),
                                  context_instance=RequestContext(request),
                                  mimetype="text/plain")
    elif format == "json":
        host = request.get_host()
        results = {"newspapers": []}
        for state, titles in newspapers_by_state:
            for title in titles:
                results["newspapers"].append({"lccn": title.lccn, "title: ": title.name, "url": "http://" + host + title.json_url, "state": state})
            
        return HttpResponse(json.dumps(results, indent=2), mimetype='application/json')
    else:
        return HttpResponseServerError("unsupported format: %s" % format)        


@cache_page(settings.API_TTL_SECONDS)
def newspapers_atom(request):
    # get a list of titles with issues that are in order by when they
    # were last updated
    titles = models.Title.objects.filter(has_issues=True)
    titles = titles.annotate(last_release=Max('issues__batch__released'))
    titles = titles.order_by('-last_release')

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

@cors
@cache_page(settings.DEFAULT_TTL_SECONDS)
@opensearch_clean
def search_titles_results(request):
    page_title = 'US Newspaper Directory Search Results'
    crumbs = [
        {'label':'Search Newspaper Directory',
         'href': urlresolvers.reverse('chronam_search_titles')},
        ]
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

    try:
        rows = int(request.REQUEST.get('rows', '20'))
    except ValueError, e:
        rows = 20

    query = request.GET.copy()
    query.rows = rows
    if page.has_next():
        query['page'] = curr_page + 1
        next_url = '?' + query.urlencode()
    if page.has_previous():
        query['page'] = curr_page - 1
        previous_url = '?' + query.urlencode()
    start = page.start_index()
    end = page.end_index()
    host = request.get_host()
    page_list = []
    for p in range(len(page.object_list)):
        page_start = start+p
        page_list.append((page_start, page.object_list[p]))
    format = request.GET.get('format', None)
    if format == 'atom':
        feed_url = 'http://' + host + request.get_full_path()
        updated = rfc3339(datetime.datetime.now())
        return render_to_response('search_titles_results.xml',
                                  dictionary=locals(),
                                  context_instance=RequestContext(request),
                                  mimetype='application/atom+xml')

    elif format == 'json':
        results = {
            'startIndex': start ,
            'endIndex': end,
            'totalItems': paginator.count,
            'itemsPerPage': rows,
            'items': [t.solr_doc for t in page.object_list]
        }
        # add url for the json view
        for i in results['items']:
            i['url'] = 'http://' + request.get_host() + i['id'].rstrip("/") + ".json"
        json_text = json.dumps(results, indent=2)
        # jsonp?
        if request.GET.get('callback') != None:
            json_text = "%s(%s);" % (request.GET.get('callback'), json_text)
        return HttpResponse(json_text, mimetype='application/json')

    sort = request.GET.get('sort', 'relevance')

    q = request.GET.copy()
    if 'page' in q:
        del q['page']
    if 'sort' in q:
        del q['sort']
    q = q.urlencode()
    collapse_search_tab = True 
    return render_to_response('search_titles_results.html',
                              dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
@rdf_view
def newspapers_rdf(request):
    titles = models.Title.objects.filter(has_issues=True)
    graph = titles_to_graph(titles)
    return HttpResponse(graph.serialize(base=_rdf_base(request),
                                        include_base=True),
                        mimetype='application/rdf+xml')
