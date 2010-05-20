import logging

from django.core.management.base import BaseCommand
    
from chronam.utils import configure_logging
from chronam.web.index import index_titles

configure_logging("index_logging.config", "index.log")

_logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "index all titles and pages ; " + \
           "you may (or may not) want to zap_index before"

    def handle(self, **options):

        _logger.info("indexing titles")
        index_titles()
        _logger.info("finished indexing titles")

        _logger.info("indexing pages")
        index_pages()
        _logger.info("finished indexing pages")

