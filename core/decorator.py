import re
from functools import wraps

from django.core import urlresolvers
from django.http import HttpResponse
from django.utils import cache, encoding
from mimeparse import best_match


class HttpResponseSeeOther(HttpResponse):
    status_code = 303

    def __init__(self, redirect_to):
        HttpResponse.__init__(self)
        self["Location"] = encoding.iri_to_uri(redirect_to)


class HttpResponseUnsupportedMediaType(HttpResponse):
    status_code = 415


# TODO: replace this with the standard Django 1.10+ cache_control decorator
def add_cache_headers(ttl, shared_cache_maxage=None):
    """Decorate the provided function by adding Cache-Control and Expires headers to responses"""

    def decorator(function):
        if not hasattr(function, "__name__"):
            function.__name__ = function.__class__.__name__

        @wraps(function)
        def decorated_function(*args, **kwargs):
            response = function(*args, **kwargs)
            cache.patch_response_headers(response, ttl)
            maxage = ttl if shared_cache_maxage is None else shared_cache_maxage
            cache.patch_cache_control(response, public=True, s_maxage=maxage)
            return response

        return decorated_function

    return decorator


def opensearch_clean(f):
    """
    Some opensearch clients send along optional parameters from the opensearch
    description when they're not needed. For example:

        state={chronam:state?}

    These can cause search results not to come back, and even can cause Solr's
    query parsing to throw an exception, so it's best to remove them when
    present.
    """

    @wraps(f)
    def f1(request, **kwargs):
        new_get = request.GET.copy()
        for k, v in new_get.items():
            if type(v) == unicode and re.match(r"^\{.+\?\}$", v):
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

    @wraps(f)
    def new_f(*args, **kwargs):
        response = f(*args, **kwargs)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "X-requested-with"
        return response

    return new_f
