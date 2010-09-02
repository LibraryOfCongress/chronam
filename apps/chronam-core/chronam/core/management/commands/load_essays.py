import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from chronam.core.essay_loader import load_essay
from chronam.core.management.commands import configure_logging


configure_logging("load_essays.config", 'load_essays.log')

class Command(BaseCommand):
    help = "load all the essays"

    def handle(self, *args, **options):
        for essay_file in os.listdir(settings.ESSAY_STORAGE):
            load_essay(essay_file)
