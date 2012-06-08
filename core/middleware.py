import os

from django.conf import settings
from django.http import HttpResponse


class HttpResponseServiceUnavailable(HttpResponse):
    status_code = 503


class TooBusyMiddleware(object):

    def process_request(self, request):
        one, five, fifteen = os.getloadavg()
        if one > settings.TOO_BUSY_LOAD_AVERAGE:
            return HttpResponseServiceUnavailable()
        return None
