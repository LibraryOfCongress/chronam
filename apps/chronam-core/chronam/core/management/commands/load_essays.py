import os
import logging

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from chronam.core.essay_loader import load_essay
from chronam.core.management.commands import configure_logging


configure_logging("load_essays.config", 'load_essays.log')
log = logging.getLogger()

class Command(BaseCommand):
    help = "load all the essays"

    def handle(self, *args, **options):
        essay_files = os.listdir(settings.ESSAY_STORAGE)
        essay_files.sort()

        for essay_file in essay_files:
            if "template.html" in essay_file:
                continue
            try:
                load_essay(essay_file)
            except Exception, e:
                log.error("unable to load essay %s: %s" % (essay_file, e))
