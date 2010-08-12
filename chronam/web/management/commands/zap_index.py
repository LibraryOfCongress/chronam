import optparse

from django.core.management.base import BaseCommand
from django.conf import settings

from solr import SolrConnection


class Command(BaseCommand):
    batch_option = optparse.make_option('--batch', 
        action = 'store',
        dest = 'batch', 
        help='the batch name for pages you want to purge from index')
    option_list = BaseCommand.option_list + (batch_option,)
    help = "remove all documents, or only documents related to a particular batch from the solr index"
    args = 'an optional batch'

    def handle(self, **options):
        solr = SolrConnection(settings.SOLR)
        if options['batch']:
            solr.delete_query('batch: %s' % options['batch'])
        else:
            solr.delete_query('id:[* TO *]')
        solr.commit()
