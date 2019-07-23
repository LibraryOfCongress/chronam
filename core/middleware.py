# encoding: utf-8
import logging
import os

from django.conf import settings
from django.http import HttpResponse

from chronam.core.utils.utils import add_cache_tag


class CloudflareCacheHeader(object):
    def process_response(self, request, response):
        return add_cache_tag(response, "project=chronam")


class HttpResponseServiceUnavailable(HttpResponse):
    status_code = 503


class TooBusyMiddleware(object):
    BUSY_MESSAGE = u"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Server Too Busy — Chronicling America (The Library of Congress)</title>
</head>
<body>
     <article>
        <h1>Server Too Busy</h1>
        <div>
            <p>
                The Chronicling America server is currently too busy to serve your request.
                Please try your request again shortly.
            </p>
            <p>
                <a href="https://www.loc.gov/pictures/resource/ppmsc.01752/">
                    <img src="https://memory.loc.gov/service/pnp/ppmsc/01700/01752r.jpg"/>
                </a>
            </p>
        </div>
    </article>
</body>
</html>
""".strip()

    def process_request(self, request):
        # FIXME: this adds per-request file I/O which could be removed by
        # calling the Linux-specific sysinfo() call directly or simply by removing
        # it and letting Varnish handle erroring backends at that level

        try:
            one, five, fifteen = os.getloadavg()
            too_busy = one > settings.TOO_BUSY_LOAD_AVERAGE
        except OSError:
            logging.exception("os.getloadavg() failed!")
            too_busy = True

        if too_busy:
            return HttpResponseServiceUnavailable(self.BUSY_MESSAGE)
