import logging

from datetime import datetime
import os
from optparse import make_option

from django.core.management.base import BaseCommand

from openoni.core import title_loader
from openoni.core.index import index_titles
from openoni.core.models import Title
from openoni.core.management.commands import configure_logging

configure_logging('load_titles_logging.config', 'load_titles.log')
_logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Load a marcxml file of title records"
    args = '<location of marcxml>'
    option_list = BaseCommand.option_list + (
        make_option('--skip-index',
        action='store_true',
        dest='skip_index',
        default=False,
        help="\
                Skip the index process. Use this if you call this from \
                another process such as 'openoni_sync'. If you call this \
                directly, you don't want to use this flag. \
            "),
    )

    def __init__(self):
        super(Command, self).__init__()
        self.total_processed = 0
        self.total_created = 0
        self.total_updated = 0
        self.total_errors = 0
        self.total_missing_lccns = 0
        self.files_processed = 0
        self.start_time = datetime.now()
        self.xml_start = datetime.now()

    def xml_file_handler(self, marc_xml, skip_index):
        self.xml_start = datetime.now()
        results = title_loader.load(marc_xml)

        if not skip_index:
            # need to index any titles that we just created
            _logger.info("indexing new titles")
            index_titles(since=self.xml_start)
        
        return results

    def add_results(self, results):
        '''
        The add results functions adds the new set of results to the
        running totals for the current run & retuns the new results set.
        '''
        self.total_processed += results[0]
        self.total_created += results[1]
        self.total_updated += results[2]
        self.total_errors += results[3]
        self.total_missing_lccns += results[4]

    def log_stats(self):
        _logger.info("############### TOTAL RESULTS ############")
        _logger.info("TITLE RECORDS PROCESSED: %i" % self.total_processed)
        _logger.info("NEW TITLES CREATED: %i" % self.total_created)
        _logger.info("EXISTING TITLES UPDATED: %i" % self.total_updated)
        _logger.info("ERRORS: %i" % self.total_errors)
        _logger.info("MISSING LCCNS: %i" % self.total_missing_lccns)
        _logger.info("FILES PROCESSED: %i" % self.files_processed)

        end = datetime.now()

        # Document titles that are not being updated.
        ts = Title.objects.filter(version__lt=self.start_time)
        not_updated = ts.count()
        _logger.info("TITLES NOT UPDATED: %i" % not_updated)

        # Total time to run.
        _logger.info("START TIME: %s" % str(self.start_time))
        _logger.info("END TIME: %s" % str(end))
        total_time = end - self.start_time
        _logger.info("TOTAL TIME: %s" % str(total_time))

    def handle(self, marc_xml_source, *args, **options):
        skip_index = options['skip_index']

        # check if arg passed is a file or a directory of files
        if os.path.isdir(marc_xml_source):
            marc_xml_dir = os.listdir(marc_xml_source)

            for xml_file in marc_xml_dir:
                results = None
                xml_file_path = os.path.join(marc_xml_source, xml_file)
                results = self.xml_file_handler(xml_file_path, skip_index)
                total_results = self.add_results(results)
                self.files_processed += 1

            self.log_stats()

        else:
            results = self.xml_file_handler(marc_xml_source, skip_index)
