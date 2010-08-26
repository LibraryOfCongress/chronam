from django.utils import encoding
from django.http import HttpResponse

class HttpResponseSeeOther(HttpResponse):
    status_code = 303

    def __init__(self, redirect_to):
        HttpResponse.__init__(self)
        self['Location'] = encoding.iri_to_uri(redirect_to)

class HttpResponseUnsupportedMediaType(HttpResponse):
    status_code = 415


