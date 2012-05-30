import random
import datetime

from django.http import Http404, HttpResponse
from django.template import RequestContext
from django.template.loader import get_template
from django.core import urlresolvers
from django.core.cache import cache

from chronam.core import models
from chronam.core.decorator import profile


def home(request, date=None):
    context = RequestContext(request, {})

    if date is None:
        date = datetime.date.today()
        date = datetime.date(date.year - 100, date.month, date.day)
    else:
        _year, _month, _day = date.split("-")
        try:
            date = datetime.date(int(_year), int(_month), int(_day))
        except ValueError, e:
            raise Http404
    
    results = cache.get(date)
    if results is None:
        results = []
        issues = models.Issue.objects.filter(date_issued=date)
        for issue in issues:
            first_page = issue.first_page
            if not first_page or not first_page.jp2_filename:
                continue
            path_parts = dict(lccn=issue.title.lccn,
                              date=date,
                              edition=issue.edition,
                              sequence=first_page.sequence)
            url = urlresolvers.reverse('chronam_page',
                                       kwargs=path_parts)
            thumbnail_url = urlresolvers.reverse('chronam_page_thumbnail',
                                       kwargs=path_parts)
            results.append({
                    'label': "%s" % issue.title.name,
                    'url': url,
                    'thumbnail_url': thumbnail_url,
                    'place_of_publication': issue.title.place_of_publication,
                    'pages': issue.pages.count()})
        cache.set(date, results, 600)        
    random.shuffle(results)
    context['results'] = results
    context['date'] = date
    template = get_template('home.html')
    context['page_title'] = "Historic American Newspapers"
    context['page_count'] = len(results)
    return HttpResponse(content=template.render(context))
