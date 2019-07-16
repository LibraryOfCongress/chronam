from __future__ import absolute_import

import logging
from timeit import default_timer

from django.conf import settings
from solr import SolrConnection

from . import LoggingCommand

LOGGER = logging.getLogger(__name__)


class Command(LoggingCommand):
    help = "Optimize Solr Index"  # NOQA: A003

    def handle(self, *args, **options):
        self.stdout.write("Optimizing Solr index %s" % settings.SOLR)
        solr = SolrConnection(settings.SOLR)
        start_time = default_timer()
        solr.optimize()
        elapsed = default_timer() - start_time
        self.stdout.write("Solr took %0.3f seconds to optimize %s" % (elapsed, settings.SOLR))
