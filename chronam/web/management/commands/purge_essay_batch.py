import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from chronam.web.essay_loader import EssayLoader
from chronam.utils import configure_logging


configure_logging("purge_essay_batch_logging.config", 'purge_essay_batch.log')

class Command(BaseCommand):
    help = "purge a batch of essays"
    args = "<batch name>"

    def handle(self, batch_dir, *args, **options):
        if len(args) != 0:
            raise CommandError("Usage is purge_essay_batch %s" % self.args)

        batch_dir = os.path.join(settings.ESSAY_STORAGE, batch_dir)
        if not os.path.isdir(batch_dir):
            raise CommandError("not finding batch at %s" % batch_dir)

        loader = EssayLoader()
        loader.purge(batch_dir)
        print "deleted essays for: %s" % loader.deletes
