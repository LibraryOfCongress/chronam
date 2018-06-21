"""
This management command is designed to be run just before a data release to the
public. It sets the 'release' date on the batches, and also generates up to date
sitemap files for crawlers.
"""

import re
import logging
import os
import csv

from optparse import make_option
from time import mktime
from datetime import datetime

import feedparser

from django.core.management.base import BaseCommand
from django.conf import settings

from chronam.core.rdf import rdf_uri
from chronam.core import models as m

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Updates (Resets if --reset option is used) release datetime on batches from one of following sources (in order of preference) 1. bag-info.txt, if found in the batch source 2. If path to a file is provided with the command, datetime is extracted from the file 3. current public feed 4. current server datetime"

    reset = make_option('--reset',
        action = 'store_true',
        dest = 'reset',
        default = False,
        help = 'reset release times to nothing before setting them again')
    option_list = BaseCommand.option_list + (reset, )

    def handle(self, *args, **options):
        if options['reset']:
            for batch in m.Batch.objects.all():
                batch.released = None
                LOGGER.info("unsetting release time for %s" % batch.name)
                batch.save()

        input_file_path = None
        if args and os.path.isfile(args[0]):
            LOGGER.info("using file %s for release dates", args[0])
            input_file_path = args[0]               
            # turn content from input file into a dictionary for easy lookup
            batch_release_from_file = preprocess_input_file(input_file_path)

        # turn content from public feed into a dictionary for easy lookup
        batch_release_from_feed = preprocess_public_feed()

        for batch in m.Batch.objects.filter(released__isnull=True):
            if os.path.isfile('%s/%s/bag-info.txt' % (settings.BATCH_STORAGE, batch.name)):
                # if released datetime is successfully set from the bag-info file,
                # move on to the next batch, else try other options
                if set_batch_released_from_bag_info(batch):
                    LOGGER.info("set release datetime from bag-info file") 
                    continue
            if input_file_path:
                batch_release_datetime = batch_release_from_file.get(batch.name, None)
                if batch_release_datetime:
                    batch.released = batch_release_datetime
                    batch.save()
                    continue
            batch_release_datetime = batch_release_from_feed.get(batch.name, None)
            if batch_release_datetime:
                LOGGER.info("set release datetime from feed for %s", batch.name)
                batch.released = batch_release_datetime
                batch.save()
                continue
            # well, none of the earlier options worked, current timestamp it is.
            LOGGER.info("couldn't determine the release time, so using current time")
            batch.released = datetime.now()
            batch.save()


def preprocess_input_file(file_path):
    """
    Input file format: batch_name\tbatch_date\n - one batch per line
    """
    batch_release_times = {}
    try:
        tsv = csv.reader(open(file_path, 'rb'), delimiter='\t')
        for row in tsv:
            batch_release_times[row[0]] = row[1]
    except: 
        pass
    return batch_release_times



def preprocess_public_feed():
    """
    reads the public feed - http://chroniclingamerica.loc.gov/batches/feed/
    and returns a dictionary of {batch name: released datetime}
    """
    LOGGER.info("processing public feed for released datetime")
    feed = feedparser.parse("http://chroniclingamerica.loc.gov/batches/feed/")
    batch_release_times = {}

    if len(feed.entries) == 0:
        LOGGER.error("public feed did not return any batches! Check to make sure chroniclingamerica.loc.gov is running correctly")

    cont = True
    while cont:
        for entry in feed.entries:
            batch_name = re.match(r'info:lc/ndnp/batch/(.+)', entry.id).group(1)
            # convert time.struct from feedparser into a datetime for django
            released = datetime.fromtimestamp(mktime(entry.updated_parsed))
            batch_release_times[batch_name] = released
            #if the batch starts with batch_ remove it, so that it works regardless of that prefix
            if batch_name.startswith("batch_"):
                batch_release_times[batch_name[6:]] = released

        next_page = get_next_page(feed)
        if next_page:
            feed = feedparser.parse(next_page)
        else:
            cont = False
    return batch_release_times


def get_next_page(feed):
    for link in feed.feed.links:
        if link.rel == 'next':
            return link.href
    return None


def set_batch_released_from_bag_info(batch):
    status = False
    bag_info = open(('%s/%s/bag-info.txt' % (settings.BATCH_STORAGE, batch.name)), 'r')
    for line in bag_info.readlines():
        # if the key release date is specified at in bag-info.txt changes, edit
        # the line below.
        if 'lc-accept-date' in line:
            batch.released = datetime.strptime(line.split(': ')[1], '%Y-%m-%d')
            batch.save()
            status = True
    bag_info.close()
    return status
