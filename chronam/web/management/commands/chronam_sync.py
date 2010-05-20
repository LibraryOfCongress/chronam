import os
import logging

from optparse import make_option

from django.core import management
from django.core.management.base import BaseCommand
import simplejson

from chronam.web import models
from chronam.web.title_loader import TitleLoader
from chronam.web.essay_loader import EssayLoader
from chronam.web.holding_loader import HoldingLoader
from chronam.web.index import index_titles
from chronam.utils import configure_logging
from chronam.settings import BIB_STORAGE, ESSAY_STORAGE

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
        management.call_command('loaddata', 'languages.json')
        management.call_command('loaddata', 'institutions.json')
        management.call_command('loaddata', 'ethnicities.json')
        management.call_command('loaddata', 'labor_presses.json')
        management.call_command('loaddata', 'countries.json')

        # look in BIB_STORAGE for titles to load
        title_loader = TitleLoader()
        for filename in os.listdir(BIB_STORAGE): 
            if filename.startswith('titles-') and filename.endswith('.xml'):
                title_loader.main(os.path.join(BIB_STORAGE, filename))

        # look in BIB_STORAGE for holdings files to load 
        # NOTE: must run after titles are all loaded or else they may 
        # not link up properly
        holding_loader = HoldingLoader()
        for filename in os.listdir(BIB_STORAGE):
            if filename.startswith('holdings-') and filename.endswith('.xml'):
                holding_loader.main(os.path.join(BIB_STORAGE, filename))

        # overlay place info harvested from dbpedia onto the places table
        self.load_place_links()

        for batch_name in os.listdir(ESSAY_STORAGE):
            batch_dir = os.path.join(ESSAY_STORAGE, batch_name)
            loader = EssayLoader()            
            try:
                loader.load(batch_dir)
            except Exception, e:
                _logger.exception(e)

        index_titles()
        _logger.info("chronam_sync done.")

    def load_place_links(self):
        _logger.info('loading place links')
        for p in simplejson.load(file('web/fixtures/place_links.json')):
            place = models.Place.objects.get(name=p['name'])
            place.longitude = p['longitude']
            place.latitude = p['latitude']
            place.geonames = p['geonames']
            place.dbpedia = p['dbpedia']
            place.save()
        _logger.info('finished loading place links')

