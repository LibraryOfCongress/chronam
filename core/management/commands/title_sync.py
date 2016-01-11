import os
import logging
from datetime import datetime, timedelta
from optparse import make_option

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

try:
    import simplejson as json
except ImportError:
    import json

from openoni import core
from openoni.core import index
from openoni.core.essay_loader import load_essays
from openoni.core.management.commands import configure_logging
from openoni.core.models import Place, Title
from openoni.core.utils.utils import validate_bib_dir

configure_logging("title_sync_logging.config", "title_sync.log")
_logger = logging.getLogger(__name__)


class Command(BaseCommand):
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

    option_list = BaseCommand.option_list + (skip_essays, pull_title_updates)

    help = 'Runs title pull and title load for a complete title refresh.'
    args = ''

    def find_titles_not_updated(self, limited=True):
        _logger.info("Looking for titles not yet updated.")

        if Title.objects.count() == 0:
            _logger.info("Total number of titles not updated: 0")
            return Title.objects.values()
        elif limited:
            titles = Title.objects.order_by('-version').values(
                'lccn_orig', 'oclc', 'version')
            end = titles[0]['version']
        else:
            titles = Title.objects.order_by('-version')
            end = titles[0].version

        start = end - timedelta(weeks=2)
        titles = titles.exclude(version__range=(start, end))

        _logger.info("Total number of titles not updated: %s" % len(titles))
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

        _logger.info("Starting title sync process.")
        # only load titles if the BIB_STORAGE is there, not always the case
        # for folks in the opensource world
        bib_in_settings = validate_bib_dir()
        if bib_in_settings:
            worldcat_dir = bib_in_settings + '/worldcat_titles/'

            pull_titles = bool(options['pull_title_updates'] and hasattr(settings, "WORLDCAT_KEY"))
            if pull_titles:
                call_command('pull_titles',)

            _logger.info("Starting load of OCLC titles.")
            bulk_dir = worldcat_dir + 'bulk'
            if os.path.isdir(bulk_dir):
                call_command('load_titles', bulk_dir, skip_index=True)

            tnu = self.find_titles_not_updated()

            # Only update by individual lccn if there are records that need updating.
            if pull_titles and len(tnu):
                _logger.info("Pulling titles from OCLC by individual lccn & oclc num.")
                self.pull_lccn_updates(tnu)

            _logger.info("Loading titles from second title pull.")
            lccn_dir = worldcat_dir + 'lccn'
            if os.path.isdir(lccn_dir):
                call_command('load_titles', lccn_dir, skip_index=True)

            tnu = self.find_titles_not_updated(limited=False)
            _logger.info("Running pre-deletion checks for these titles.")

        # Make sure that our essays are up to date
        if not options['skip_essays']:
            load_essays(settings.ESSAYS_FEED)

        if bib_in_settings:
            if len(tnu):
                # Delete titles haven't been update & do not have essays or issues attached.
                for title in tnu:
                    essays = title.essays.all()
                    issues = title.issues.all()

                    error = "DELETION ERROR: Title %s has " % title
                    error_end = "It will not be deleted."

                    if not essays or not issues:
                        delete_txt = (title.name, title.lccn, title.oclc)
                        _logger.info('TITLE DELETED: %s, lccn: %s, oclc: %s' % delete_txt)
                        title.delete()
                    elif essays:
                        _logger.warning(error + 'essays.' + error_end)
                        continue
                    elif issues:
                        _logger.warning(error + 'issues.' + error_end)
                        continue

            # Load holdings for all remaining titles.
            call_command('load_holdings')

        # overlay place info harvested from dbpedia onto the places table
        try:
            self.load_place_links()
        except Exception, e:
            _logger.exception(e)

        index.index_titles()

        # Time of full process run
        end = datetime.now()
        total_time = end - start
        _logger.info('start time: %s' % start)
        _logger.info('end time: %s' % end)
        _logger.info('total time: %s' % total_time)
        _logger.info("title_sync done.")

    def load_place_links(self):
        _logger.info('loading place links')
        _CORE_ROOT = os.path.abspath(os.path.dirname(core.__file__))
        filename = os.path.join(_CORE_ROOT, './fixtures/place_links.json')
        for p in json.load(file(filename)):
            place = Place.objects.get(name=p['name'])
            place.longitude = p['longitude']
            place.latitude = p['latitude']
            place.geonames = p['geonames']
            place.dbpedia = p['dbpedia']
            place.save()
        _logger.info('finished loading place links')
