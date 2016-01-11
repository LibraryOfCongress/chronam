import logging

from datetime import datetime
from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings

from openoni.core import title_pull

from openoni.core.management.commands import configure_logging
    
configure_logging('pull_titles_logging.config', 'pull_titles.log')
_logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Retrieve a fresh pull of titles from OCLC. \
            #TODO: add a list of example commands."
    args = ''
    #TODO: Remove default from lccn
    option_list = BaseCommand.option_list + (
        make_option('-l', '--lccn',
        action='store',
        dest='lccn',
        default=None,
        help="Pass a specific lccn to pull down updates from Worldcat."),

        make_option('-o', '--oclc',
        action='store',
        dest='oclc',
        default=None,
        help="Pass an oclc number when you pass an lccn."),

        make_option('-p','--path',
        action='store',
        dest='path',
        default='/worldcat_titles/',
        help="Path var that is appeneded to settings.BIB_STORAGE to save to"),
    )

    def run_pull(self, path, lccn=None, oclc=None, query=None):
        start = datetime.now()
        search = title_pull.TitlePuller()
        save_path = settings.BIB_STORAGE + path
        search.run(save_path, lccn, oclc, query)
        end = datetime.now()
        return start, end

    def handle(self, **options):
        lccn = options['lccn']
        oclc = options['oclc']
        path = options['path']

        if lccn:
            start, end = self.run_pull(path + '/lccn/', lccn, oclc)
            if start and end:
                _logger.info("lccn: %s, oclc: %s" % (lccn, oclc))
        else:
            _logger.info("started pulling titles from OCLC.")
            start, end = self.run_pull(path + 'bulk/') 
            _logger.info("finished pulling titles from OCLC.")
            _logger.info("start time: %s" % start)
            _logger.info("end time: %s" % end)

        total = end - start
        _logger.info("total time: %s" % total)
        _logger.info("#######################################")
