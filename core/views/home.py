import json
import random
import datetime

from django.conf import settings
from django.http import Http404, HttpResponse
from django.template import RequestContext
from django.template.loader import get_template
from django.core import urlresolvers
from django.core.cache import cache
from django.shortcuts import render_to_response

from chronam.core import models
from chronam.core.decorator import profile

def home(request, date=None):
    context = RequestContext(request, {})
    context["total_page_count"] = models.Page.objects.all().count()
    context["crumbs"] = list(settings.BASE_CRUMBS)
    template = get_template("home.html")
    # note the date is handled on the client side in javascript
    return HttpResponse(content=template.render(context))

def frontpages(request, date):
    _year, _month, _day = date.split("-")
    try:
        date = datetime.date(int(_year), int(_month), int(_day))
    except ValueError, e:
        raise Http404
    
    results = []
    for issue in models.Issue.objects.filter(date_issued=date):
        first_page = issue.first_page
        if not first_page or not first_page.jp2_filename:
            continue

        path_parts = dict(lccn=issue.title.lccn,
                          date=issue.date_issued,
                          edition=issue.edition,
                          sequence=first_page.sequence)
        url = urlresolvers.reverse('chronam_page', kwargs=path_parts)
        thumbnail_url = urlresolvers.reverse('chronam_page_thumbnail', kwargs=path_parts)
        results.append({
            'label': "%s" % issue.title.display_name,
            'url': url,
            'thumbnail_url': thumbnail_url,
            'place_of_publication': issue.title.place_of_publication,
            'pages': issue.pages.count()})
 
    return HttpResponse(json.dumps(results), mimetype="application/json")


def tabs(request, date=None):
    context = RequestContext(request, {})
    template = get_template("includes/tabs.html")
    return HttpResponse(content=template.render(context))
