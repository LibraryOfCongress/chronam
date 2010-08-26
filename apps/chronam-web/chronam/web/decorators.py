import re

from django.core import urlresolvers
from chronam.utils.mimeparse import best_match

from chronam.web import responses

def rdf_view(f):
    def f1(request, **kwargs):
        # construct a http redirect response to html view
        html_view = f.func_name.replace('_rdf', '')
        html_url = urlresolvers.reverse('chronam_%s' % html_view, kwargs=kwargs)
        html_redirect = responses.HttpResponseSeeOther(html_url)

        # determine the clients preferred representation
        available = ['text/html', 'application/rdf+xml']
        accept = request.META.get('HTTP_ACCEPT', 'application/rdf+xml')
        match = best_match(available, accept)

        # figure out what user agent we are talking to
        ua = request.META.get('HTTP_USER_AGENT')

        if request.get_full_path().endswith('.rdf'):
            return f(request, **kwargs)
        elif ua and 'MSIE' in ua:
            return html_redirect
        elif match == 'application/rdf+xml':
            response = f(request, **kwargs)
            response['Vary'] = 'Accept'
            return response
        elif match == 'text/html':
            return html_redirect 
        else:
            return responses.HttpResponseUnsupportedMediaType()
    return f1

def opensearch_clean(f):
    """
    Some opensearch clients send along optional parameters from the opensearch
    description when they're not needed. For example:
    
        state={chronam:state?}

    These can cause search results not to come back, and even can cause Solr's 
    query parsing to throw an exception, so it's best to remove them when
    present.
    """
    def f1(request, **kwargs):
        new_get = request.GET.copy()
        for k, v in new_get.items():
            if type(v) == unicode and re.match(r'^\{.+\?\}$', v):
                new_get.pop(k)
        request.GET = new_get
        return f(request, **kwargs)
    return f1
