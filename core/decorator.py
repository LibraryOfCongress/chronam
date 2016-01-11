import os
import re
import time
import hotshot

from mimeparse import best_match

from django.utils import cache
from django.utils import encoding
from django.http import HttpResponse
from django.core import urlresolvers


class HttpResponseSeeOther(HttpResponse):
    status_code = 303

    def __init__(self, redirect_to):
        HttpResponse.__init__(self)
        self['Location'] = encoding.iri_to_uri(redirect_to)


class HttpResponseUnsupportedMediaType(HttpResponse):
    status_code = 415



def cache_page(ttl):
    def decorator(function):
        def decorated_function(*args, **kwargs):
            request = args[0]
            response = function(*args, **kwargs)
            cache.patch_response_headers(response, ttl)
            return response
        return decorated_function
    return decorator

def rdf_view(f):
    def f1(request, **kwargs):
        # construct a http redirect response to html view
        html_view = f.func_name.replace('_rdf', '')
        html_url = urlresolvers.reverse('openoni_%s' % html_view, kwargs=kwargs)
        html_redirect = HttpResponseSeeOther(html_url)

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
            return HttpResponseUnsupportedMediaType()
    return f1

def opensearch_clean(f):
    """
    Some opensearch clients send along optional parameters from the opensearch
    description when they're not needed. For example:
    
        state={openoni:state?}

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

def cors(f, *args, **kwargs):
    """
    Adds CORS header to allow a response to be loaded by JavaScript that 
    may have originated from somewhere other than chroniclingamerica.loc.gov
    which is useful for some API response like AutoSuggest. Basically allows
    developers to use our JSON in their JavaScript applications without
    forcing them to proxy it.
    """
    def new_f(*args, **kwargs):
        response = f(*args, **kwargs)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Headers'] = 'X-requested-with'
        return response
    return new_f

try:
    PROFILE_LOG_BASE = settings.PROFILE_LOG_BASE
except:
    PROFILE_LOG_BASE = '/tmp'

def profile(log_file):
    if not os.path.isabs(log_file):
        log_file = os.path.join(PROFILE_LOG_BASE, log_file)

    def _outer(f):
        def _inner(*args, **kwargs):
            (base, ext) = os.path.splitext(log_file)
            base = base + "-" + time.strftime("%Y%m%dT%H%M%S", time.gmtime())
            final_log_file = base + ext

            prof = hotshot.Profile(final_log_file)
            try:
                ret = prof.runcall(f, *args, **kwargs)
            finally:
                prof.close()
            return ret

        return _inner
    return _outer

