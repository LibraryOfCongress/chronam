from __future__ import absolute_import

from chronam.core.index import index_missing_pages

from . import LoggingCommand


class Command(LoggingCommand):
    def handle(self, **options):
        index_missing_pages()
