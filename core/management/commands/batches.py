from __future__ import absolute_import, print_function

from chronam.core import models

from . import LoggingCommand


class Command(LoggingCommand):
    help = "Displays information about batches"
    args = ''

    def handle(self, *args, **options):

        for batch in models.Batch.objects.all().order_by('name'):
            self.stdout.write(batch.name)
