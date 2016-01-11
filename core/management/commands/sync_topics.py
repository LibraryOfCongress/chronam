import logging

from django.core import management
from django.core.management.base import BaseCommand

from openoni.core import models
from openoni.core.management.commands import configure_logging
from openoni.core import topic_loader


configure_logging("openoni_sync_logging.config", "openoni_sync.log")
_logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = ''
    args = ''

    def handle(self, **options):
        topic_loader.load_topic_and_categories()
