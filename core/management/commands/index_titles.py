import logging

from django.core.management.base import BaseCommand

from chronam.core.index import index_titles

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, **options):
        LOGGER.info("indexing titles")
        index_titles()
        LOGGER.info("finished indexing titles")

