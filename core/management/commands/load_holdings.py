import logging
import os

from django.core import management
from django.core.management.base import BaseCommand

from openoni.core import models
from openoni.core.holding_loader import HoldingLoader
from openoni.core.management.commands import configure_logging
from openoni.core.utils.utils import validate_bib_dir

configure_logging('load_holdings_logging.config', 'load_holdings.log')
_logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Load a holdings records after title records are all loaded"
    args = '<location of holdings directory>'

    bib_in_settings = validate_bib_dir()
    if bib_in_settings:
        default_location = bib_in_settings + '/holdings'
    else:
        default_location = None

    def handle(self, holdings_source=default_location, *args, **options):
        
        if not os.path.exists(holdings_source): 
            _logger.error("There is no valid holdings source folder defined.")
            set_holdings = ['To load holdings - Add a folder called "holdings"',
            'to the bib directory that is set in settings',
            'or pass the location of holdings as an arguement to the loader.',]
            _logger.error(' '.join(set_holdings))
            return

        # First we want to make sure that our material types are up to date
        material_types = models.MaterialType.objects.all()
        [m.delete() for m in material_types]
        management.call_command('loaddata', 'material_types.json')
       
        holding_loader = HoldingLoader()
        holding_loader.main(holdings_source)
