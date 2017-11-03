import logging

from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError

_logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Purge the django cache after ingest/purge of a batch"

    def handle(self, *args, **options):

        try:
            # delete the total pages count
            _logger.info('removing newspaper_info from cache')
            cache.delete('newspaper_info')

            # delete the advanced search title list
            _logger.info('removing titles_states from cache')
            cache.delete('titles_states')
	
	    # delete the fulltext date range
            _logger.info('removing fulltext_range')
            cache.delete('fulltext_range')


        except Exception, e:
            _logger.exception(e)
            raise CommandError("unable to purge the cache. check the purge_batch_cache log for clues")
