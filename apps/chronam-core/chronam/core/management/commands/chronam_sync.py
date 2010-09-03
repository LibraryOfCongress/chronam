import os
import logging

from optparse import make_option

from django.core import management
from django.core.management.base import BaseCommand
from django.conf import settings

try:
    import simplejson as json
except ImportError:
    import json

from chronam import core
from chronam.core import models
from chronam.core import index
from chronam.core.title_loader import TitleLoader
from chronam.core.essay_loader import load_essay
from chronam.core.holding_loader import HoldingLoader
from chronam.core.management.commands import configure_logging

configure_logging("chronam_sync_logging.config", "chronam_sync.log")
_logger = logging.getLogger(__name__)


class Command(BaseCommand):
    verbose = make_option('--verbose',
        action = 'store_true',
        dest = 'verbose',
        default = False,
        help = '')
    option_list = BaseCommand.option_list + (verbose, )
    help = ''
    args = ''

    def handle(self, **options):
        if not (models.Title.objects.all().count() and \
                models.Holding.objects.all().count() and \
                models.Essay.objects.all().count() and \
                models.Batch.objects.all().count() and \
                models.Issue.objects.all().count() and \
                models.Page.objects.all().count() and \
                index.page_count() and \
                index.title_count()):
            _logger.warn("Database or index not empty as expected.")
            return

        management.call_command('loaddata', 'languages.json')
        management.call_command('loaddata', 'institutions.json')
        management.call_command('loaddata', 'ethnicities.json')
        management.call_command('loaddata', 'labor_presses.json')
        management.call_command('loaddata', 'countries.json')

        # look in BIB_STORAGE for titles to load
        title_loader = TitleLoader()
        for filename in os.listdir(settings.BIB_STORAGE): 
            if filename.startswith('titles-') and filename.endswith('.xml'):
                title_loader.main(os.path.join(settings.BIB_STORAGE, filename))

        # look in BIB_STORAGE for holdings files to load 
        # NOTE: must run after titles are all loaded or else they may 
        # not link up properly
        holding_loader = HoldingLoader()
        for filename in os.listdir(settings.BIB_STORAGE):
            if filename.startswith('holdings-') and filename.endswith('.xml'):
                holding_loader.main(
                    os.path.join(settings.BIB_STORAGE, filename))

        # overlay place info harvested from dbpedia onto the places table
        self.load_place_links()

        for essay_file in os.listdir(settings.ESSAY_STORAGE):
            try:
                load_essay(essay_file)
            except Exception, e:
                _logger.exception(e)

        index.index_titles()
        _logger.info("chronam_sync done.")

    def load_place_links(self):
        _logger.info('loading place links')
        _CORE_ROOT = os.path.abspath(os.path.dirname(core.__file__))
        filename= os.path.join(_CORE_ROOT, './fixtures/place_links.json')
        for p in json.load(file(filename)):
            place = models.Place.objects.get(name=p['name'])
            place.longitude = p['longitude']
            place.latitude = p['latitude']
            place.geonames = p['geonames']
            place.dbpedia = p['dbpedia']
            place.save()
        _logger.info('finished loading place links')

