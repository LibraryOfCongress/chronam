import os
import logging

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from chronam.core.batch_loader import BatchLoader, BatchLoaderException
from chronam.utils import configure_logging
    
configure_logging('purge_batches_logging.config', 
                  'purge_batch_%s.log' % os.getpid())

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Purge a batch"
    args = '<batch_location>'

    def handle(self, batch_location=None, *args, **options):
        if len(args)!=0:
            raise CommandError('Usage is purge_batch %s' % self.args)

        loader = BatchLoader()
        try:
            loader.purge_batch(batch_location)
        except BatchLoaderException, e:
            LOGGER.exception(e)
            raise CommandError("unable to purge batch. check the purge_batch log for clues")
