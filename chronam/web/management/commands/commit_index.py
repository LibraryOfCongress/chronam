from django.core.management.base import BaseCommand, CommandError
from solr import SolrConnection

from chronam.settings import SOLR

class Command(BaseCommand):
    help = "send a commit message to the solr index"

    def handle(self, **options):
        solr = SolrConnection(SOLR)
        solr.commit()
