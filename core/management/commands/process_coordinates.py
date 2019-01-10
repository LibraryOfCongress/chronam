import logging
import os

from django.core.management.base import BaseCommand, CommandError

from chronam.core import batch_loader

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process word coordinates for a batch by name from a batch list file"
    args = "<batch_list_filename>"

    def handle(self, batch_list_filename, *args, **options):
        if len(args) != 0:
            raise CommandError("Usage is process_coordinates %s" % self.args)

        verbosity = options["verbosity"]

        if verbosity > 0:
            log_level = logging.DEBUG if verbosity > 1 else logging.INFO
            loggers = [logging.getLogger(), logging.getLogger("chronam")]
            for logger in loggers:
                logger.setLevel(log_level)
                for handler in logger.handlers:
                    handler.setLevel(log_level)

        loader = batch_loader.BatchLoader()

        if os.path.exists(batch_list_filename):
            with open(batch_list_filename) as f:
                batches = [i.strip() for i in f]
        else:
            batches = [batch_list_filename]

        LOGGER.info("Processing %d batches from %s", len(batches), batch_list_filename)

        for batch_name in batches:
            LOGGER.info("batch_name: %s" % batch_name)
            loader.process_coordinates(batch_name)
