from __future__ import absolute_import

import optparse

from django.conf import settings
from solr import SolrConnection

from . import LoggingCommand


class Command(LoggingCommand):
    batch_option = optparse.make_option(
        '--batch', action='store', dest='batch', help='the batch name for pages you want to purge from index'
    )
    option_list = LoggingCommand.option_list + (batch_option,)
    help = (  # NOQA: A003
        "remove all documents, or only documents related to a particular batch from the solr index"
    )
    args = 'an optional batch'

    def handle(self, **options):
        solr = SolrConnection(settings.SOLR)
        if options['batch']:
            solr.delete_query('batch: %s' % options['batch'])
        else:
            solr.delete_query('id:[* TO *]')
        solr.commit()
