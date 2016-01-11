import logging

from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError

from openoni.core.management.commands import configure_logging

configure_logging('', 'purge_django_cache.log' )

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Purge the django cache after ingest/purge of a batch"

    def handle(self, *args, **options):

        try:
            # delete the total pages count
            LOGGER.info('removing newspaper_info from cache')
            cache.delete('newspaper_info')

            # delete the advanced search title list
            LOGGER.info('removing titles_states from cache')
            cache.delete('titles_states')

        except Exception, e:
            LOGGER.exception(e)
            raise CommandError("unable to purge the cache. check the purge_batch_cache log for clues")
