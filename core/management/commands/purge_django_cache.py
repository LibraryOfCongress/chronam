from __future__ import absolute_import

import logging
from optparse import make_option

from django.core.cache import cache
from django.core.management.base import CommandError

from . import LoggingCommand

LOGGER = logging.getLogger(__name__)


class Command(LoggingCommand):
    purge_all = make_option(
        '--all',
        action='store_true',
        dest='purge_all',
        default=False,
        help='Purge everything from the django cache',
    )

    option_list = LoggingCommand.option_list + (purge_all,)
    help = "Purge the django cache after ingest/purge of a batch"  # NOQA: A003

    def handle(self, *args, **options):
        try:
            if options['purge_all']:
                LOGGER.info("clearing the whole django cache")
                cache.clear()
            else:
                # delete the cached newspaper statistics
                LOGGER.info('removing newspaper_info from cache')
                cache.delete('newspaper_info')

                # delete the advanced search title list
                LOGGER.info('removing titles_states from cache')
                cache.delete('titles_states')

                # delete the fulltext date range
                LOGGER.info('removing fulltext_range')
                cache.delete('fulltext_range')
        except Exception:
            LOGGER.exception('Unable to purge cache')
            raise CommandError("unable to purge the cache. check the purge_batch_cache log for clues")
