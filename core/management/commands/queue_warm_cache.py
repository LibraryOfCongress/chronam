import logging

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from chronam.core.models import Page
from chronam.core import tasks

_logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Queue a celery request for each page from chronicling america to warm up the cache."

    def handle(self, **options):
        for page in Page.objects.all():
	    try:
                url = "https://chroniclingamerica.loc.gov%s" % page.url
                _logger.info("queuing url %s"% url)
                tasks.load_page_in_cache.delay(url)
            except Exception, e:
                _logger.exception(e)
                raise CommandError("Unable to queue warm cache request. Check the log for clues.")
