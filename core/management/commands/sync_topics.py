import logging

from django.core import management
from django.core.management.base import BaseCommand

from chronam.core import models
from chronam.core.management.commands import configure_logging
from chronam.core import topic_loader


configure_logging("chronam_sync_logging.config", "chronam_sync.log")
_logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = ''
    args = ''

    def handle(self, **options):
        topic_loader.load_topic_and_categories()
