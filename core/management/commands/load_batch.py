from __future__ import absolute_import

import logging
import os
from optparse import make_option

from django.core.management.base import CommandError

from chronam.core.batch_loader import BatchLoader

from . import LoggingCommand

LOGGER = logging.getLogger(__name__)


class Command(LoggingCommand):
    option_list = LoggingCommand.option_list + (
        make_option(
            "--skip-process-ocr",
            action="store_false",
            dest="process_ocr",
            default=True,
            help="Do not generate ocr, and index",
        ),
        make_option(
            "--skip-coordinates",
            action="store_false",
            dest="process_coordinates",
            default=True,
            help="Do not out word coordinates",
        ),
    )
    help = "Load a batch"  # NOQA: A003
    args = "<batch path>"

    def handle(self, batch_path, *args, **options):
        if len(args) != 0:
            raise CommandError("Usage is load_batch %s" % self.args)

        if not os.path.isdir(batch_path):
            raise CommandError("Path %s does not exist" % batch_path)

        batch_path = os.path.realpath(batch_path)

        loader = BatchLoader(
            process_ocr=options["process_ocr"], process_coordinates=options["process_coordinates"]
        )

        try:
            loader.load_batch(batch_path)
        except Exception:
            LOGGER.exception("Unable to load batch from %s", batch_path)
