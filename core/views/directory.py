import csv
import datetime
import json
from rfc3339 import rfc3339

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseServerError
from django.db.models import Max, Min, Q
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.encoding import smart_str

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
            state = state.title()
    else:
        state = request.REQUEST.get('state', None)

    language = request.REQUEST.get('language', None)
    if language:
        language_display = models.Language.objects.get(code__contains=language).name
    ethnicity = request.REQUEST.get('ethnicity', None)

    if not state and not language and not ethnicity:
        page_title = 'All Digitized Newspapers'
    else:
        page_title = 'Results: Digitized Newspapers'

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

    newspapers_by_state = [(s, sorted(t, key=lambda title: title.name_normal)) for s, t in sorted(_newspapers_by_state.iteritems())]
    crumbs = list(settings.BASE_CRUMBS)

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
    elif format == "csv":
        csv_header_labels = ('Persistent Link', 'State', 'Title', 'LCCN', 'OCLC', 
                             'ISSN', 'No. of Issues', 'First Issue Date', 
                             'Last Issue Date', 'More Info')
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="chronam_newspapers.csv"'
        writer = csv.writer(response)
        writer.writerow(csv_header_labels)
        for state, titles in newspapers_by_state:
            for title in titles:
                writer.writerow(('http://%s%s' % (request.get_host(), 
                                                  reverse('chronam_issues', 
                                                           kwargs={'lccn': title.lccn}),),
                                 state, title, title.lccn or '', title.oclc or '',
                                 title.issn or '', title.issues.count(), title.first, 
                                 title.last, 
                                 'http://%s%s' % (request.get_host(),
                                                  reverse('chronam_title_essays',
                                                           kwargs={'lccn': title.lccn}),),))
        return response

    elif format == "json":
        host = request.get_host()
        results = {"newspapers": []}
        for state, titles in newspapers_by_state:
            for title in titles:
                results["newspapers"].append({
                    "lccn": title.lccn,
                    "title": title.display_name,
                    "url": "http://" + host + title.json_url,
                    "state": state
                })

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
    crumbs = list(settings.BASE_CRUMBS)
    crumbs.extend([{'label': 'Search Newspaper Directory',
                    'href': reverse('chronam_search_titles')},
                   ])

    def prep_title_for_return(t):
        title = {}
        title.update(t.solr_doc)
        title['oclc'] = t.oclc
        return title

    format = request.GET.get('format', None)

    # check if requested format is CSV before building pages for response. CSV 
    # response does not make use of pagination, instead all matching titles from
    # SOLR are returned at once
    if format == 'csv':
        query = request.GET.copy()
        q, fields, sort_field, sort_order, facets = index.get_solr_request_params_from_query(query)
        
        # return all titles in csv format. * May hurt performance. Assumption is that this
        # request is not made often. 
        # TODO: revisit if assumption is incorrect
        solr_response = index.execute_solr_query(q, fields, sort_field, 
                                                 sort_order, index.title_count(), 0)
        titles = index.get_titles_from_solr_documents(solr_response)

        csv_header_labels = ('lccn', 'title', 'place_of_publication', 'start_year',
                             'end_year', 'publisher', 'edition', 'frequency', 'subject', 
                             'state', 'city', 'country', 'language', 'oclc',
                             'holding_type',)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="chronam_titles.csv"'
        writer = csv.writer(response)
        writer.writerow(csv_header_labels)
        for title in titles:
            writer.writerow(map(lambda val: smart_str(val or '--'),
                               (title.lccn, title.name, title.place_of_publication,
                                title.start_year, title.end_year, title.publisher, 
                                title.edition, title.frequency, 
                                map(str, title.subjects.all()), 
                                set(map(lambda p: p.state, title.places.all())), 
                                map(lambda p: p.city, title.places.all()),
                                str(title.country), map(str, title.languages.all()),
                                title.oclc, title.holding_types)))
        return response
 
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

    if format == 'atom':
        feed_url = 'http://' + host + request.get_full_path()
        updated = rfc3339(datetime.datetime.now())
        return render_to_response('search_titles_results.xml',
                                  dictionary=locals(),
                                  context_instance=RequestContext(request),
                                  mimetype='application/atom+xml')

    elif format == 'json':
        results = {
            'startIndex': start,
            'endIndex': end,
            'totalItems': paginator.count,
            'itemsPerPage': rows,
            'items': [prep_title_for_return(t) for t in page.object_list]
        }
        # add url for the json view
        for i in results['items']:
            i['url'] = 'http://' + request.get_host() + i['id'].rstrip("/") + ".json"
        json_text = json.dumps(results, indent=2)
        # jsonp?
        if request.GET.get('callback') is not None:
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
