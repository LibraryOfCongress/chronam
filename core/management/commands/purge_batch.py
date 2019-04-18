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
            '--no-optimize',
            action='store_false',
            dest='optimize',
            default=True,
            help='Do not optimize Solr and MySQL after purge',
        ),
    )
    help = "Purge a batch"
    args = '<batch_location>'

    def handle(self, batch_location=None, *args, **options):
        if len(args) != 0:
            raise CommandError('Usage is purge_batch %s' % self.args)

        loader = BatchLoader()
        try:
            LOGGER.info("purging batch %s", batch_location)
            loader.purge_batch(batch_location)
            if options['optimize']:
                LOGGER.info("optimizing solr")
                solr = SolrConnection(settings.SOLR)
                solr.optimize()
                LOGGER.info("optimizing MySQL OCR table")
                cursor = connection.cursor()
                cursor.execute("OPTIMIZE TABLE core_ocr")
                LOGGER.info("finished optimizing")
        except BatchLoaderException as e:
            LOGGER.exception(e)
            raise CommandError("unable to purge batch. check the log for clues")
