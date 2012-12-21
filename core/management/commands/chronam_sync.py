import os
import logging
from datetime import datetime
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
from chronam.core import title_loader
from chronam.core.essay_loader import load_essays
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
        if not (models.Title.objects.all().count()==0 and \
                models.Holding.objects.all().count()==0 and \
                models.Essay.objects.all().count()==0 and \
                models.Batch.objects.all().count()==0 and \
                models.Issue.objects.all().count()==0 and \
                models.Page.objects.all().count()==0 and \
                index.page_count()==0 and \
                index.title_count()==0):
            _logger.warn("Database or index not empty as expected.")
            return

        start = datetime.now()
        management.call_command('loaddata', 'languages.json')
        management.call_command('loaddata', 'institutions.json')
        management.call_command('loaddata', 'ethnicities.json')
        management.call_command('loaddata', 'labor_presses.json')
        management.call_command('loaddata', 'countries.json')

        # only load titles if the BIB_STORAGE is there, not always the case
        # for folks in the opensource world
        if hasattr(settings, "BIB_STORAGE") and os.path.isdir(settings.BIB_STORAGE):
            # look in BIB_STORAGE for original titles to load
            for filename in os.listdir(settings.BIB_STORAGE): 
                if filename.startswith('titles-') and filename.endswith('.xml'):
                    filepath = os.path.join(settings.BIB_STORAGE, filename)
                    title_loader.load(filepath, skip_index=True)

            _logger.info('Starting OCLC title update.')
            worldcat_path = settings.BIB_STORAGE + '/worldcat_titles/'
            management.call_command('load_titles', worldcat_path, skip_index=True)

            # look in BIB_STORAGE for holdings files to load 
            # NOTE: must run after titles are all loaded or else they may 
            # not link up properly
            holding_loader = HoldingLoader()
            for filename in os.listdir(settings.BIB_STORAGE):
                if filename.startswith('holdings-') and filename.endswith('.xml'): 
                    holding_loader.main(
                        os.path.join(settings.BIB_STORAGE, filename))

        # overlay place info harvested from dbpedia onto the places table
        try:
            self.load_place_links()
        except Exception, e:
            _logger.exception(e)

        load_essays(settings.ESSAYS_FEED)
       
        # We wait to index all the titles at the end.
        index.index_titles()

        end = datetime.now()
        total_time = start - end
        _logger.info('start time: %s' % start)
        _logger.info('end time: %s' % end)
        _logger.info('total time: %s' % total_time)
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

