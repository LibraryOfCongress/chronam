import calendar
import datetime
import os
import wsgiref.util

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.core import urlresolvers
from django.http import HttpResponse, Http404
from django.utils.http import http_date
from django.utils import datetime_safe

from openoni.core import models


def _rdf_base(request):
    host = request.get_host()
    path = request.get_full_path().rstrip(".rdf")
    return "http://%s%s" % (host, path)


def _page_range_short(paginator, page):
    middle = 3
    for p in paginator.page_range:
        if p <= 3:
            yield p
        elif paginator.num_pages - p < 3:
            yield p
        elif abs(p - page.number) < middle:
            yield p
        elif abs(p - page.number) == middle:
            yield "..."


class HTMLCalendar(calendar.Calendar):
    """
    This calendar returns complete HTML pages.
    """

    def __init__(self, firstweekday=0, issues=None):
        calendar.Calendar.__init__(self, firstweekday)
        self.issues = issues

    # CSS classes for the day <td>s
    cssclasses = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

    def formatday(self, year, month, day, weekday):
        """
        Return a day as a table cell.
        """
        if day == 0:
            return '<td class="noday">&nbsp;</td>'  # day outside month
        else:
            r = self.issues.filter(date_issued=datetime.date(year, month, day))
            issues = set()
            for issue in r:
                issues.add((issue.title.lccn,
                            issue.date_issued, issue.edition))
            issues = sorted(list(issues))
            count = len(issues)
            if count == 1:
                _class = "single"
                lccn, date_issued, edition = issues[0]
                kw = dict(lccn=lccn, date=date_issued, edition=edition)
                url = urlresolvers.reverse('openoni_issue_pages', kwargs=kw)
                _day = """<a href="%s">%s</a>""" % (url, day)
            elif count > 1:
                _class = "multiple"
                _day = "<em class='text-info'>%s </em>" % day
                _day += "<ul class='unstyled'>"
                for lccn, date_issued, edition in issues:
                    kw = dict(lccn=lccn, date=date_issued, edition=edition)
                    url = urlresolvers.reverse('openoni_issue_pages',
                                               kwargs=kw)
                    _day += """<li><a href="%s">ed-%d</a></li>""" % (url, edition)
                _day += "</ul>"
            else:
                _class = "noissues"
                _day = day
            return '<td class="%s %s">%s</td>' % (_class,
                                                  self.cssclasses[weekday],
                                                  _day)

    def formatweek(self, year, month, theweek):
        """
        Return a complete week as a table row.
        """
        s = ''.join(self.formatday(year, month, d, wd) for (d, wd) in theweek)
        return '<tr>%s</tr>' % s

    def formatweekday(self, day):
        """
        Return a weekday name as a table header.
        """
        return '<td class="dayname %s">%s</td>' % (self.cssclasses[day],
                                                   calendar.day_abbr[day][0])

    def formatweekheader(self):
        """
        Return a header for a week as a table row.
        """
        s = ''.join(self.formatweekday(i) for i in self.iterweekdays())
        return '<tr class="daynames">%s</tr>' % s

    def formatmonthname(self, theyear, themonth, withyear=True):
        """
        Return a month name as a table row.
        """
        if withyear:
            s = '%s %s' % (calendar.month_name[themonth], theyear)
        else:
            s = '%s' % calendar.month_name[themonth]
        return '<tr><td colspan="7" class="title">%s, %s</td></tr>' % (s,
                                                                       theyear)

    def formatmonth(self, theyear, themonth, withyear=True):
        """
        Return a formatted month as a table.
        """
        v = []
        a = v.append
        a('<table border="0" cellpadding="0" cellspacing="0" class="month table table-condensed table-bordered">')
        a('\n')
        a(self.formatmonthname(theyear, themonth, withyear=withyear))
        a('\n')
        a(self.formatweekheader())
        a('\n')
        weeks = self.monthdays2calendar(theyear, themonth)
        while len(weeks) < 6:
            # add blank weeks so all calendars are 6 weeks long.
            weeks.append([(0, 0)] * 7)
        for week in weeks:
            a(self.formatweek(theyear, themonth, week))
            a('\n')
        a('</table>')
        a('\n')
        return ''.join(v)

    def formatyear(self, theyear, width=4):
        """
        Return a formatted year as a div of tables.
        """
        v = []
        a = v.append
        width = max(width, 1)
        a('<div cellspacing="0" class="calendar_wrapper">')
        for i in range(calendar.January, calendar.January + 12, width):
            # months in this row
            months = range(i, min(i + width, 13))
            a('<div class="calendar_row">')
            for m in months:
                a('<div class="span3 calendar_month">')
                a(self.formatmonth(theyear, m, withyear=False))
                a('</div>')
            a('</div>')
        a('</div>')
        return ''.join(v)


def get_page(lccn, date, edition, sequence):
    """a helper function to lookup a particular page based on metadata
    cooked into the openoni URLs, and raise a 404 appropriately when
    portions of the hiearchical metadata are not found in the database
    """

    _year, _month, _day = date.split("-")
    try:
        _date = datetime.date(int(_year), int(_month), int(_day))
    except ValueError, e:
        raise Http404
    try:
        page = models.Page.objects.filter(
            issue__title__lccn=lccn,
            issue__date_issued=_date,
            issue__edition=edition,
            sequence=sequence).order_by("-created").select_related()[0]
        return page
    except IndexError, e:
        raise Http404


def _get_tip(lccn, date, edition, sequence=1):
    """a helper function to lookup a particular page based on metadata cooked
    into the openoni URLs, and raise a 404 appropriately when portions of the
    hiearchical metadata are not found in the database
    """
    title = get_object_or_404(models.Title, lccn=lccn)
    _year, _month, _day = date.split("-")
    try:
        _date = datetime.date(int(_year), int(_month), int(_day))
    except ValueError, e:
        raise Http404
    try:
        issue = title.issues.filter(
            date_issued=_date, edition=edition).order_by("-created")[0]
    except IndexError, e:
        raise Http404
    try:
        page = issue.pages.filter(
            sequence=int(sequence)).order_by("-created")[0]
    except IndexError, e:
        raise Http404
    return title, issue, page


def _stream_file(path, mimetype):
    """helper function for streaming back the contents of a file"""
    # must calculate Content-length else django ConditionalGetMiddleware
    # tries to and fails, since it is streaming back, and it attempts to
    # calculate len() on the response content!
    if path:
        stat = os.stat(path)
        r = HttpResponse(wsgiref.util.FileWrapper(file(path)))
        r['Content-Type'] = mimetype
        r['Content-Length'] = stat.st_size
        r['Last-Modified'] = http_date(stat.st_mtime)
        return r
    else:
        raise Http404


def label(instance):
    if isinstance(instance, models.Title):
        return u'%s (%s) %s-%s' % (instance.display_name,
                                   instance.place_of_publication,
                                   instance.start_year, instance.end_year)
    elif isinstance(instance, models.Issue):
        parts = []
        dt = datetime_safe.new_datetime(instance.date_issued)
        parts.append(dt.strftime('%B %d, %Y'))
        if instance.edition_label:
            parts.append(u"%s" % instance.edition_label)
        return u', '.join(parts)
    elif isinstance(instance, models.Page):
        parts = []
        if instance.section_label:
            parts.append(instance.section_label)
        if instance.number:
            parts.append('Page %s' % instance.number)
        parts.append('Image %s' % instance.sequence)
        return u', '.join(parts)
    else:
        return u"%s" % instance


def create_crumbs(title, issue=None, date=None, edition=None, page=None):
    crumbs = list(settings.BASE_CRUMBS)
    crumbs.extend([{'label': label(title.name.split(":")[0]),
                    'href': urlresolvers.reverse('openoni_title',
                                                 kwargs={'lccn': title.lccn})}])
    if date and edition is not None:
        crumbs.append(
            {'label': label(issue),
             'href': urlresolvers.reverse('openoni_issue_pages',
                                          kwargs={'lccn': title.lccn,
                                                  'date': date,
                                                  'edition': edition})})

    if page is not None:
        crumbs.append(
            {'label': label(page),
             'href': urlresolvers.reverse('openoni_page',
                                          kwargs={'lccn': title.lccn,
                                                  'date': date,
                                                  'edition': edition,
                                                  'sequence': page.sequence})})

    return crumbs


def validate_bib_dir():
    bib_isdir = os.path.isdir(settings.BIB_STORAGE)
    bib_hasattr = hasattr(settings, "BIB_STORAGE")
    bib_in_settings = bool(bib_hasattr and bib_isdir)
    if bib_in_settings:
        return settings.BIB_STORAGE
    else:
        return None
