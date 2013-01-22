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

from chronam import core
from chronam.core import index
from chronam.core.essay_loader import load_essays
from chronam.core.management.commands import configure_logging
from chronam.core.models import Place, Title


configure_logging("title_sync_logging.config", "title_sync.log")
_logger = logging.getLogger(__name__)


class Command(BaseCommand):
    skip_essays = make_option('--skip-essays',
                              action='store_true',
                              dest='skip_essays',
                              default=False,
                              help='Skip essay loading.')
    option_list = BaseCommand.option_list + (skip_essays,)

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

        _logger.info("Starting title sync process.")
        # only load titles if the BIB_STORAGE is there, not always the case
        # for folks in the opensource world
        bib_isdir = os.path.isdir(settings.BIB_STORAGE)
        bib_hasattr = hasattr(settings, "BIB_STORAGE")
        bib_settings = bool(bib_hasattr and bib_isdir)
        if bib_settings:
            bib_storage = settings.BIB_STORAGE
            ##call_command('pull_titles',)

            _logger.info("Starting load of OCLC titles.")
            worldcat_path = bib_storage + '/worldcat_titles/'
            call_command('load_titles', worldcat_path + 'bulk', skip_index=True)

            _logger.info("Looking for titles not updated in the bulk OCLC pull.")
            tnu = self.find_titles_not_updated()
            _logger.info("After bulk OCLC pull and load: %s not updated." % len(tnu))

            if len(tnu):
                _logger.info("Pulling titles from OCLC by individual lccn & oclc num.")
                self.pull_lccn_updates(tnu)

                _logger.info("Loading titles from second title pull.")
                call_command('load_titles', worldcat_path + 'lccn', skip_index=True)

                _logger.info("Looking for titles that were not found in OCLC updates.")
                tnu = self.find_titles_not_updated(limited=False)
                _logger.info("%s titles not in OCLC updates." % len(tnu))
                _logger.info("Running pre-deletion checks for these titles.")

        # Make sure that our essays are up to date
        if not options['skip_essays']:
            load_essays(settings.ESSAYS_FEED)

        if bib_settings:
            if len(tnu):
                # Delete titles haven't been update & do not have essays or issues attached.
                for title in tnu:
                    essays = title.essays.all()
                    issues = title.issues.all()

                    error = "DELETION ERROR: Title %s has " % title
                    error_end = "It will not be deleted."

                    if not essays or not issues:
                        delete_txt = (str(title), title.lccn, title.oclc)
                        _logger.info('DELETE TITLE: %s, lccn: %s, oclc: %s' % delete_txt)
                        title.delete()
                    elif essays:
                        _logger.warning(error + 'essays.' + error_end)
                        continue
                    elif issues:
                        _logger.warning(error + 'issues.' + error_end)
                        continue

            # Load holdings for all remaining titles.
            holdings_dir = settings.BIB_STORAGE + '/holdings'
            call_command('load_holdings', holdings_dir)

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
