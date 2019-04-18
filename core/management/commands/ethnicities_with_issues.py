from __future__ import absolute_import, print_function

from chronam.core import models

from . import LoggingCommand


class Command(LoggingCommand):
    def handle(self, *args, **options):
        for e in models.Ethnicity.objects.all():
            print(e.name, ": ", e.has_issues)
