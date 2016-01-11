import os
import logging
from datetime import datetime
from optparse import make_option

from django.core import management
from django.core.management.base import BaseCommand

from openoni.core import models
from openoni.core import index
from openoni.core.management.commands import configure_logging
from openoni.core.utils.utils import validate_bib_dir

configure_logging("openoni_sync_logging.config", "openoni_sync.log")
_logger = logging.getLogger(__name__)

class Command(BaseCommand):
    verbose = make_option('--verbose',
                          action='store_true',
                          dest='verbose',
                          default=False,
                          help='')

    skip_essays = make_option('--skip-essays',
                              action='store_true',
                              dest='skip_essays',
                              default=False,
                              help='Skip essay loading.')

    pull_title_updates = make_option('--pull-title-updates',
                                     action='store_true',
                                     dest='pull_title_updates',
                                     default=False,
                                     help='Pull down a new set of titles.')

    option_list = BaseCommand.option_list + (verbose, skip_essays, pull_title_updates)
    help = ''
    args = ''

    def handle(self, **options):
        if not (models.Title.objects.all().count() == 0 and
                models.Holding.objects.all().count() == 0 and
                models.Essay.objects.all().count() == 0 and
                models.Batch.objects.all().count() == 0 and
                models.Issue.objects.all().count() == 0 and
                models.Page.objects.all().count() == 0 and
                index.page_count() == 0 and
                index.title_count() == 0):
            _logger.warn("Database or index not empty as expected.")
            return

        start = datetime.now()
        management.call_command('loaddata', 'languages.json')
        management.call_command('loaddata', 'institutions.json')
        management.call_command('loaddata', 'ethnicities.json')
        management.call_command('loaddata', 'labor_presses.json')
        management.call_command('loaddata', 'countries.json')

        bib_in_settings = validate_bib_dir()
        if bib_in_settings:
            # look in BIB_STORAGE for original titles to load
            for filename in os.listdir(bib_in_settings):
                if filename.startswith('titles-') and filename.endswith('.xml'):
                    filepath = os.path.join(bib_in_settings, filename)
                    management.call_command('load_titles', filepath, skip_index=True)

        management.call_command('title_sync',
                                skip_essays=options['skip_essays'],
                                pull_title_updates=options['pull_title_updates'])

        end = datetime.now()
        total_time = end - start
        _logger.info('start time: %s' % start)
        _logger.info('end time: %s' % end)
        _logger.info('total time: %s' % total_time)
        _logger.info("openoni_sync done.")
