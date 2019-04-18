from __future__ import absolute_import

from django.core.management.base import BaseCommand

from chronam.core.index import index_pages


class Command(BaseCommand):

    def handle(self, **options):
        index_pages()
