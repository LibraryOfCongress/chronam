"""
This management command is designed to be run just before a data release to the
public. It sets the 'release' date on the batches, and also generates up to date
sitemap files for crawlers.
"""

import re
import logging

from optparse import make_option
from time import mktime
from datetime import datetime

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from django.db import reset_queries

from chronam.utils import configure_logging, feedparser
from chronam.utils.rfc3339 import rfc3339
from chronam.web import models as m
from chronam.web.rdf import rdf_uri

configure_logging("release.config", "release.log")

_logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Prepares for a data release by setting the released datetime on batches that lack them using the current public feed of batches or the current time. This command also writes out sitemap files to the static directory."
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
    sitemap_index = open('static/sitemaps/index.xml', 'w')
    sitemap_index.write('<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')

    max_urls = 50000
    page_count = 0
    url_count = 0
    sitemap_file = None

    for loc, last_mod in sitemap_urls():

        # if we've maxed out the number of urls per sitemap 
        # close out the one we have open and open a new one
        if url_count % max_urls == 0:
            page_count += 1
            if sitemap_file: 
                sitemap.write('</urlset>\n')
                sitemap.close()
            sitemap_file = 'sitemap-%05d.xml' % page_count
            sitemap_path = 'static/sitemaps/%s' % sitemap_file
            _logger.info("writing %s" % sitemap_path)
            sitemap = open(sitemap_path, 'w')
            sitemap.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            sitemap_index.write('<sitemap><loc>http://chroniclingamerica.loc.gov/sitemaps/%s</loc></sitemap>\n' % sitemap_file)
    
        # add a url to the sitemap
        sitemap.write("<url><loc>http://chroniclingamerica.loc.gov%s</loc><lastmod>%s</lastmod></url>\n" % (loc, rfc3339(last_mod)))
        url_count += 1

        # necessary to avoid memory bloat when chronam.settings.DEBUG = True
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
        yield batch.url, batch.released
        yield rdf_uri(batch), batch.released
        for issue in batch.issues.all():
            yield issue.url, batch.released
            yield rdf_uri(issue), batch.released
            for page in issue.pages.all():
                yield page.url, batch.released
                yield rdf_uri(page), batch.released

    paginator = Paginator(m.Title.objects.all(), 10000)
    for page_num in range(1, paginator.num_pages + 1):
        page = paginator.page(page_num)
        for title in page.object_list:
            yield title.url, title.created

