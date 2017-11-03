import logging

from django.core.management.base import BaseCommand
    
from chronam.core.index import index_titles

_logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, **options):
        _logger.info("indexing titles")
        index_titles()
        _logger.info("finished indexing titles")

