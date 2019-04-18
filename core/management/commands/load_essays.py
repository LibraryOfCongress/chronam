from __future__ import absolute_import

from django.conf import settings
from django.core.management.base import BaseCommand

from chronam.core.essay_loader import load_essays


class Command(BaseCommand):
    help = "load all the essays"

    def handle(self, *args, **options):
        load_essays(settings.ESSAYS_FEED, index=True)
