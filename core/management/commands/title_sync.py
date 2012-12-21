import os
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from chronam.core import index
from chronam.core.holding_loader import HoldingLoader
from chronam.core.management.commands import configure_logging
from chronam.core.models import Title

configure_logging("title_sync_logging.config", "title_sync.log")
_logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Runs title pull and title load for a complete title refresh.'
    args = ''

    def find_titles_not_updated(self, limited=True):
        if limited:
            titles = Title.objects.order_by('-version').values(
                'lccn_orig', 'oclc', 'version')
            end = titles[0]['version']
        else:
            titles = Title.objects.order_by('-version')
            end = titles[0].version

        start = end - timedelta(weeks=1)
        titles = titles.exclude(version__range=(start, end))
        return titles

    def pull_lccn_updates(self, titles):
        start = datetime.now()
        for t in titles:
            call_command('pull_titles', lccn=t['lccn_orig'], oclc=t['oclc'])
        end = datetime.now()
        total_time = end - start
        _logger.info('total time for pull_lccn_updates: %s' % total_time)
        return

    def handle(self, *args, **options):
        start = datetime.now()

        #TODO: Reassess after we make pull_titles work
        # with states more cleanly.
        if hasattr(settings, "BIB_STORAGE") and os.path.isdir(settings.BIB_STORAGE):
            bib_storage = settings.BIB_STORAGE

            _logger.info("Starting OCLC pull.")
            #TODO: Add check to make sure that pull_titles
            # destination is empty.
            # Maybe an option to empty it otherwise the process exits?
            ###call_command('pull_titles')

            _logger.info("Starting load of OCLC titles.")
            worldcat_path = bib_storage + '/worldcat_titles/'
            call_command('load_titles', worldcat_path + 'bulk')

            _logger.info("Looking for titles not updated in the bulk OCLC pull.")
            titles_not_updated = self.find_titles_not_updated()
            tnu_count = len(titles_not_updated)
            _logger.info("After bulk OCLC pull: %s not updated." % tnu_count)

            _logger.info("Pulling titles from OCLC by individual lccn & oclc num.")
            self.pull_lccn_updates(titles_not_updated)

            _logger.info("Loading titles from second title pull.")
            call_command('load_titles', worldcat_path + 'lccn')

            _logger.info("Looking for titles that were not found in OCLC updates.")
            tnu = self.find_titles_not_updated(limited=False)
            _logger.info("%s titles not in OCLC updates." % len(tnu))
            _logger.info("Running pre-deletion checks for these titles.")

            for title in tnu:
                essays = title.essays.all()
                issues = title.issues.all()

                error = "DELETION ERROR: Title %s has" % title
                error_end = "It will not be deleted."

                if not essays or not issues:
                    title.delete()
                elif essays:
                    _logger.info(error + ' essays ' + error_end)
                    continue
                elif issues:
                    _logger.info(error + ' issues ' + error_end)
                    continue

            #TDOD: After archive & update process is updated, remove this
            # next section & add the stuff below it.
            holding_loader = HoldingLoader()
            for filename in os.listdir(bib_storage):
                if filename.startswith('holdings-') and filename.endswith('.xml'):
                    holding_loader.main(os.path.join(bib_storage, filename))

            #Add the following, make sure the directory is correct
            #holdings_dir = settings.BIB_STORAGE + '/oclcMarcHoldings/data'
            #call_command('load_holdings', holdings_dir)

        index.index_titles()

        # Time of full process run
        end = datetime.now()
        total_time = end - start
        _logger.info('start time: %s' % start)
        _logger.info('end time: %s' % end)
        _logger.info('total time: %s' % total_time)
        _logger.info("title_sync done.")
