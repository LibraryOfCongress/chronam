import os
import logging

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from openoni.core import batch_loader
from openoni.core.management.commands import configure_logging

configure_logging('process_coordinates_logging.config',
                  'process_coordinates_%s.log' % os.getpid())

_logger = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
    )
    help = "Process word coordinates for a batch by name from a batch list file"
    args = '<batch_list_filename>'

    def handle(self, batch_list_filename, *args, **options):
        if len(args)!=0:
            raise CommandError('Usage is process_coordinates %s' % self.args)

        loader = batch_loader.BatchLoader()
        batch_list = file(batch_list_filename)
        _logger.info("batch_list_filename: %s" % batch_list_filename)
        for line in batch_list:
            batch_name = line.strip()
            _logger.info("batch_name: %s" % batch_name)
            parts = batch_name.split("_")
            if len(parts)==4:
                loader.process_coordinates(batch_name, strict=False)
            else:
                _logger.warning("invalid batch name '%s'" % batch_name)

