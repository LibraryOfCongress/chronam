from __future__ import absolute_import

from django.conf import settings
from solr import SolrConnection

from . import LoggingCommand


class Command(LoggingCommand):
    help = "send a commit message to the solr index"

    def handle(self, **options):
        solr = SolrConnection(settings.SOLR)
        solr.commit()
