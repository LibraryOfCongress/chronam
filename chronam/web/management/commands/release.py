import re
import logging

from optparse import make_option
from time import mktime
from datetime import datetime

from django.core.management.base import BaseCommand

from chronam.utils import configure_logging, feedparser
from chronam.web import models as m

configure_logging("release.config", "release.log")

_logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "set the released datetime on batches that lack them using the current public feed of batches or the current time"
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
