import logging

from django.core.management.base import BaseCommand
from django.conf import settings

from chronam.core.essay_loader import load_essays
from chronam.core.management.commands import configure_logging


configure_logging("load_essays.config", 'load_essays.log')
log = logging.getLogger()

class Command(BaseCommand):
    help = "load all the essays"

    def handle(self, *args, **options):
        load_essays(settings.ESSAYS_FEED, index=True)
