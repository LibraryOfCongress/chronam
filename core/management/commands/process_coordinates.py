import os
import logging

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from chronam.core import batch_loader

LOGGER = logging.getLogger(__name__)

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
        LOGGER.info("batch_list_filename: %s" % batch_list_filename)
        for line in batch_list:
            batch_name = line.strip()
            LOGGER.info("batch_name: %s" % batch_name)
            parts = batch_name.split("_")
            if len(parts)==4:
                loader.process_coordinates(batch_name)
            else:
                LOGGER.warning("invalid batch name '%s'" % batch_name)

