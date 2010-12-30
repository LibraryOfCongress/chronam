"""
This management command is designed to be run just before a data release to the
public. It sets the 'release' date on the batches, and also generates up to date
sitemap files for crawlers.
"""

import os
import re
import logging

from time import mktime
from datetime import datetime
from optparse import make_option

import feedparser
from rfc3339 import rfc3339

from django.conf import settings
from django.db import reset_queries
from django.core.paginator import Paginator
from django.core.management.base import BaseCommand
from django.template.defaultfilters import force_escape
from django.utils import datetime_safe

from chronam.core.management.commands import configure_logging
from chronam.core import models as m
from chronam.core.rdf import rdf_uri

configure_logging("release.config", "release.log")

_logger = logging.getLogger(__name__)

def rfc3339_safe(date):
    dt = datetime_safe.new_datetime(date)
    return dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')


class Command(BaseCommand):
    help = "Prepares for a data release by setting the released datetime on batches that lack them using the current public feed of batches or the current time. This command also writes out sitemap files to the settings.DOCUMENT_ROOT directory."
    reset = make_option('--reset',
        action = 'store_true',
        dest = 'reset',
        default = False,
        help = 'reset release times to nothing before setting them again')
    option_list = BaseCommand.option_list + (reset, )

    def handle(self, **options):
        if options['reset']:
            for batch in m.Batch.objects.all():
                batch.released = None
                _logger.info("unsetting release time for %s" % batch.name)
                batch.save()

        load_release_times_from_prod()
        
        # batches that lack a release time are assumed to be released *now*
        now = datetime.now()
        for batch in m.Batch.objects.filter(released__isnull=True):
            batch.released = now
            batch.save()
            _logger.info("set batch %s release time to %s" % (batch.name, 
                batch.released))

        write_sitemaps()

def load_release_times_from_prod():
    feed = feedparser.parse("http://chroniclingamerica.loc.gov/batches.xml")
    for entry in feed.entries:
        try:
            # convert the info uri for the batch to the batch name and get it 
            batch_name = re.match(r'info:lc/ndnp/batch/(.+)', entry.id).group(1)
            batch = m.Batch.objects.get(name=batch_name)

            # if the batch already has a release date assume it's right
            if batch.released:
                continue

            # convert time.struct from feedparser into a datetime for django
            released = datetime.fromtimestamp(mktime(entry.updated_parsed))

            # save the release date from production
            batch.released = released
            batch.save()
            _logger.info("set %s release time to %s from production feed" % 
                   (batch.name, entry.modified))

        except m.Batch.DoesNotExist:
            # this can happen when there are batches in production that
            # aren't in this particular environment
            _logger.error("batch for %s not found" % entry.title)

def write_sitemaps():
    """
    This function will write a sitemap index file that references individual
    sitemaps for all the batches, issues, pages and titles that have been
    loaded.
    """
    sitemap_index = open(
        os.path.join(settings.DOCUMENT_ROOT, 'sitemap.xml'), 'w')
    sitemap_index.write('<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')

    max_urls = 50000
    page_count = 0
    url_count = 0
    sitemap_file = None

    for loc, last_mod, newspaper, pub_date, title in sitemap_urls():

        # if we've maxed out the number of urls per sitemap 
        # close out the one we have open and open a new one
        if url_count % max_urls == 0:
            page_count += 1
            if sitemap_file: 
                sitemap.write('</urlset>\n')
                sitemap.close()
            sitemap_file = 'sitemap-%05d.xml' % page_count
            _logger.info("writing %s" % sitemap_file)
            sitemap = open(os.path.join(settings.DOCUMENT_ROOT, sitemap_file), 'w')
            sitemap.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n')
            sitemap_index.write('<sitemap><loc>http://chroniclingamerica.loc.gov/%s</loc></sitemap>\n' % sitemap_file)
    
        # add a url to the sitemap
        if newspaper and pub_date and title:
            url = "<url><loc>http://chroniclingamerica.loc.gov%s</loc><lastmod>%s</lastmod><news:news><news:publication><news:name>%s</news:name><news:language>en</news:language></news:publication><news:publication_date>%s</news:publication_date><news:title>%s</news:title></news:news></url>\n" % (loc, rfc3339(last_mod), force_escape(newspaper), rfc3339_safe(pub_date), force_escape(title))
        else:
            url = "<url><loc>http://chroniclingamerica.loc.gov%s</loc><lastmod>%s</lastmod></url>\n" % (loc, rfc3339(last_mod))
        sitemap.write(url.encode("utf-8"))
        url_count += 1

        # necessary to avoid memory bloat when settings.DEBUG = True
        if url_count % 1000 == 0:
            reset_queries()

    # wrap up some open files
    sitemap.write('</urlset>\n')
    sitemap.close()
    sitemap_index.write('</sitemapindex>\n')
    sitemap_index.close()

def sitemap_urls():
    """
    A generator that returns all the urls for batches, issues, pages and
    titles, and their respective modified time as a tuple.
    """
    for batch in m.Batch.objects.all():
        yield batch.url, batch.released, None, None, None
        yield rdf_uri(batch), batch.released, None, None, None
        for issue in batch.issues.all():
            yield issue.url, batch.released, None, None, None
            yield rdf_uri(issue), batch.released, None, None, None
            for page in issue.pages.all():
                yield page.url, batch.released, page.issue.title.name, \
                      page.issue.date_issued, unicode(page)
                yield rdf_uri(page), batch.released, None, None, None

    paginator = Paginator(m.Title.objects.all(), 10000)
    for page_num in range(1, paginator.num_pages + 1):
        page = paginator.page(page_num)
        for title in page.object_list:
            yield title.url, title.created, None, None, None

