import logging

from django.core.management.base import BaseCommand
    
from openoni.core.management.commands import configure_logging
from openoni.core.index import index_titles

configure_logging("index_titles_logging.config", "index_titles.log")

_logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, **options):
        _logger.info("indexing titles")
        index_titles()
        _logger.info("finished indexing titles")

