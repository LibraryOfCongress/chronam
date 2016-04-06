import json
import datetime

from django.conf import settings
from django.http import Http404, HttpResponse
from django.template import RequestContext
from django.template.loader import get_template
from django.core import urlresolvers

from chronam.core import models
from chronam.core import forms


def home(request, date=None):
    context = RequestContext(request, {})
    context["crumbs"] = list(settings.BASE_CRUMBS)
    today = datetime.date.today()
    context["date"] = date = today.replace(year=today.year-100)
    context["pages"] = _frontpages(request, date)
    template = get_template("home.html")
    # note the date is handled on the client side in javascript
    return HttpResponse(content=template.render(context))


def _frontpages(request, date):
    # if there aren't any issues default to the first 20 which
    # is useful for testing the homepage when there are no issues
    # for a given date
    issues = models.Issue.objects.filter(date_issued=date)
    if issues.count() == 0:
        issues = models.Issue.objects.all()[0:20]

    results = []
    for issue in issues:
        first_page = issue.first_page
        if not first_page or not first_page.jp2_filename:
            continue

        path_parts = dict(lccn=issue.title.lccn,
                          date=issue.date_issued,
                          edition=issue.edition,
                          sequence=first_page.sequence)
        url = urlresolvers.reverse('chronam_page', kwargs=path_parts)
        results.append({
            'label': "%s" % issue.title.display_name,
            'url': url,
            'thumbnail_url': first_page.thumb_url,
            'medium_url': first_page.medium_url,
            'place_of_publication': issue.title.place_of_publication,
            'pages': issue.pages.count()})
    return results


def frontpages(request, date):
    _year, _month, _day = date.split("-")
    try:
        date = datetime.date(int(_year), int(_month), int(_day))
    except ValueError:
        raise Http404
    results = _frontpages(request, date)
    return HttpResponse(json.dumps(results), content_type="application/json")


def tabs(request, date=None):
    params = request.GET if request.GET else None
    form = forms.SearchPagesForm()
    adv_form = forms.AdvSearchPagesForm(params)
    context = RequestContext(request, {'search_form': form,
                                       'adv_search_form': adv_form})
    template = get_template("includes/tabs.html")
    return HttpResponse(content=template.render(context))
