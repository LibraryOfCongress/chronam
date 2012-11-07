import os

from django.conf import settings
from django.http import HttpResponse


class HttpResponseServiceUnavailable(HttpResponse):
    status_code = 503


class TooBusyMiddleware(object):

    def process_request(self, request):
        one, five, fifteen = os.getloadavg()
        if one > settings.TOO_BUSY_LOAD_AVERAGE:
            return HttpResponseServiceUnavailable("""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Server Too Busy - Chronicling America - Chronicling America (The Library of Congress)</title> 
  <style></style>
</head>
<body>
     <article>
	  <h1>Server Too Busy</h1>
	   <div>
            <p>The Chronicling America server is currently too busy to serve your request. Please try your request again shortly.</p>
            <p><a href="http://www.loc.gov/pictures/resource/ppmsc.01752/"><img src="http://lcweb2.loc.gov/service/pnp/ppmsc/01700/01752r.jpg"/></a></p>
	   </div>
     </article>
</body>
</html>
""")
        return None
