import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from chronam.core.essay_loader import EssayLoader
from chronam.utils import configure_logging


configure_logging("load_essay_batch_logging.config", 'load_essay.log')

class Command(BaseCommand):
    help = "load a batch of essays"
    args = "<batch name>"

    def handle(self, batch_dir, *args, **options):
        if len(args) != 0:
            raise CommandError("Usage is load_essay_batch %s" % self.args)

        batch_dir = os.path.join(settings.ESSAY_STORAGE, batch_dir)
        if not os.path.isdir(batch_dir):
            raise CommandError("not finding batch at %s" % batch_dir)

        loader = EssayLoader()
        loader.load(batch_dir)

        print "created essays for: %s" % loader.creates
        if len(loader.missing) > 0:
            print "missing title records for: %s" % loader.missing
