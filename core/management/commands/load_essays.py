from __future__ import absolute_import

from django.conf import settings

from chronam.core.essay_loader import load_essays

from . import LoggingCommand


class Command(LoggingCommand):
    help = "load all the essays"

    def handle(self, *args, **options):
        load_essays(settings.ESSAYS_FEED, index=True)
