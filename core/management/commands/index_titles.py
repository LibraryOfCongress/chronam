from __future__ import absolute_import

import logging

from chronam.core.index import index_titles

from . import LoggingCommand

LOGGER = logging.getLogger(__name__)


class Command(LoggingCommand):
    def handle(self, **options):
        LOGGER.info("indexing titles")
        index_titles()
        LOGGER.info("finished indexing titles")
