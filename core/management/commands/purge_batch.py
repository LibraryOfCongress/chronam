from __future__ import absolute_import

import logging
from optparse import make_option

from django.conf import settings
from django.core.management.base import CommandError
from django.db import connection
from solr import SolrConnection

from chronam.core.batch_loader import BatchLoader, BatchLoaderException

from . import LoggingCommand

LOGGER = logging.getLogger(__name__)


class Command(LoggingCommand):
    option_list = LoggingCommand.option_list + (
        make_option(
            "--no-optimize",
            action="store_false",
            dest="optimize",
            default=True,
            help="Do not optimize Solr and MySQL after purge",
        ),
    )
    help = "Purge a batch"  # NOQA: A003
    args = "<batch_name>"

    def handle(self, batch_name=None, *args, **options):
        if len(args) != 0:
            raise CommandError("Usage is purge_batch %s" % self.args)

        loader = BatchLoader()
        try:
            LOGGER.info("purging batch %s", batch_name)
            loader.purge_batch(batch_name)
            if options["optimize"]:
                LOGGER.info("optimizing solr")
                solr = SolrConnection(settings.SOLR)
                solr.optimize()
                LOGGER.info("optimizing MySQL OCR table")
                cursor = connection.cursor()
                cursor.execute("OPTIMIZE TABLE core_ocr")
                LOGGER.info("finished optimizing")
        except BatchLoaderException:
            LOGGER.exception("Unable to purge batch %s", batch_name)
            raise CommandError("unable to purge batch. check the log for clues")
