import logging

from datetime import datetime
import os

from django.core.management.base import BaseCommand

from chronam.core.holding_loader import HoldingLoader
from chronam.core.management.commands import configure_logging

configure_logging('load_holdings_logging.config', 'load_holdings.log')
_logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Load a holdings records after title records are all loaded"
    args = '<location of holdings directory>'

    def handle(self, holdings_source, *args, **options):
        holding_loader = HoldingLoader()
        holding_loader.main(holdings_source)
