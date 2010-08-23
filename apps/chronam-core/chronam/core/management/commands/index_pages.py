from django.core.management.base import BaseCommand
    
from chronam.utils import configure_logging
from chronam.web.index import index_pages

configure_logging("index_pages_logging.config", "index_pages.log")

class Command(BaseCommand):

    def handle(self, **options):
        index_pages()
