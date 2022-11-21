from __future__ import absolute_import

import logging
import os

from django.core import management

from chronam.core import models
from chronam.core.holding_loader import HoldingLoader
from chronam.core.utils.utils import validate_bib_dir

from . import LoggingCommand

LOGGER = logging.getLogger(__name__)


class Command(LoggingCommand):
    help = "Load a holdings records after title records are all loaded"  # NOQA: A003
    args = "<location of holdings directory>"

    bib_in_settings = validate_bib_dir()
    if bib_in_settings:
        default_location = bib_in_settings + "/holdings"
    else:
        default_location = None

    def handle(self, holdings_source=default_location, *args, **options):

        if not os.path.exists(holdings_source):
            LOGGER.error("There is no valid holdings source folder defined.")
            set_holdings = [
                'To load holdings - Add a folder called "holdings"',
                "to the bib directory that is set in settings",
                "or pass the location of holdings as an argument to the loader.",
            ]
            LOGGER.error(" ".join(set_holdings))
            return

        # First we want to make sure that our material types are up to date
        material_types = models.MaterialType.objects.all()
        [m.delete() for m in material_types]
        management.call_command("loaddata", "material_types.json")

        holding_loader = HoldingLoader()
        holding_loader.main(holdings_source)
