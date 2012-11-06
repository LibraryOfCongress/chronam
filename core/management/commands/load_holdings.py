import logging

from django.core import management
from django.core.management.base import BaseCommand

from chronam.core import models
from chronam.core.holding_loader import HoldingLoader
from chronam.core.management.commands import configure_logging

configure_logging('load_holdings_logging.config', 'load_holdings.log')
_logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Load a holdings records after title records are all loaded"
    args = '<location of holdings directory>'

    def handle(self, holdings_source, *args, **options):
        
        # First we want to make sure that our material types are up to date
        material_types = models.MaterialType.objects.all()
        [m.delete() for m in material_types]
        management.call_command('loaddata', 'material_types.json')
        
        holding_loader = HoldingLoader()
        holding_loader.main(holdings_source)
