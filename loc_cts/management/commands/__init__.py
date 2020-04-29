from __future__ import absolute_import

import logging

from django.core.management.base import BaseCommand


class LoggingCommand(BaseCommand):
    def execute(self, *args, **options):
        verbosity = options.get("verbosity", 0)

        if verbosity > 0:
            log_level = logging.DEBUG if verbosity > 1 else logging.INFO
            loggers = [logging.getLogger(), logging.getLogger("chronam")]
            for logger in loggers:
                logger.setLevel(log_level)
                for handler in logger.handlers:
                    handler.setLevel(log_level)

        return super(LoggingCommand, self).execute(*args, **options)
