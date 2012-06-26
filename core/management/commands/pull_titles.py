import logging

from datetime import datetime

from django.core.management.base import BaseCommand
from django.conf import settings

from chronam.core import title_pull

from chronam.core.management.commands import configure_logging
    
configure_logging('pull_titles_logging.config', 'pull_titles.log')
_logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Retrieve a fresh pull of titles from OCLC"
    args = ''

    def handle(self, *args, **options):
        start = datetime.now()
        _logger.info("started pulling titles from OCLC.")
        _logger.info("start time: %s" % start)

        search = title_pull.SearchWorldCatTitles()
        save_path = '/opt/chronam/data/worldcat_titles/'
        #save_path = settings.BIB_STORAGE + '/worldcat_titles/'
        search.run(save_path)
        _logger.info("finished pulling titles from OCLC.")
        
        end = datetime.now()
        total = end - start
        _logger.info("end time: %s" % end)
        _logger.info("total time: %s" % total)
