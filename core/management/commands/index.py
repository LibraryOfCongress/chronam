from __future__ import absolute_import

import logging

from django.core.management.base import BaseCommand

from chronam.core.index import index_pages, index_titles

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "index all titles and pages ; " + \
           "you may (or may not) want to zap_index before"

    def handle(self, **options):

        LOGGER.info("indexing titles")
        index_titles()
        LOGGER.info("finished indexing titles")

        LOGGER.info("indexing pages")
        index_pages()
        LOGGER.info("finished indexing pages")
