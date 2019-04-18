from __future__ import absolute_import

import logging

from chronam.core.index import index_pages, index_titles

from . import LoggingCommand

LOGGER = logging.getLogger(__name__)


class Command(LoggingCommand):
    help = "index all titles and pages ; " + "you may (or may not) want to zap_index before"

    def handle(self, **options):

        LOGGER.info("indexing titles")
        index_titles()
        LOGGER.info("finished indexing titles")

        LOGGER.info("indexing pages")
        index_pages()
        LOGGER.info("finished indexing pages")
