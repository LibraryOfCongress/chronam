import re
from functools import wraps

from django.core import urlresolvers
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import cache, encoding
from django.views.decorators.vary import vary_on_headers
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


def rdf_view(rdf_view_func):
    @wraps(rdf_view_func)
    def inner(request, **kwargs):
        # The RDF views which have an extension are not negotiated so they can
        # be processed and cached simply:
        if request.path.endswith(".rdf"):
            return rdf_view_func(request, **kwargs)
        else:
            return negotiate_rdf_response(rdf_view_func, request, **kwargs)

    return inner


@vary_on_headers("Accept", "User-Agent")
def negotiate_rdf_response(rdf_view_func, request, **kwargs):
    # construct a http redirect response to html view
    html_view = rdf_view_func.func_name.replace("_rdf", "")
    html_url = urlresolvers.reverse("chronam_%s" % html_view, kwargs=kwargs)
    html_redirect = HttpResponseSeeOther(html_url)

    # determine the clients preferred representation
    available = ["text/html", "application/rdf+xml"]
    accept = request.META.get("HTTP_ACCEPT", "application/rdf+xml")

    try:
        match = best_match(available, accept)
    except ValueError:
        return HttpResponseBadRequest()

    if "MSIE" in request.META.get("HTTP_USER_AGENT", ""):
        return html_redirect
    elif match == "application/rdf+xml":
        return rdf_view_func(request, **kwargs)
    elif match == "text/html":
        return html_redirect
    else:
        return HttpResponseUnsupportedMediaType()


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
            if type(v) == str and re.match(r"^\{.+\?\}$", v):
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


def robots_tag(f, tags=("noindex", "nofollow"), *args, **kwargs):
    """
    Set the X-Robots-Tag header on a response to tell robots how to process the
    results.

    https://developers.google.com/search/docs/advanced/robots/robots_meta_tag
    """

    @wraps(f)
    def new_f(*args, **kwargs):
        response = f(*args, **kwargs)
        response["X-Robots-Tag"] = ", ".join(tags)
        return response

    return new_f
