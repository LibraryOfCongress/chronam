from __future__ import absolute_import

import logging
from timeit import default_timer

from django.db import connection

from . import LoggingCommand

LOGGER = logging.getLogger(__name__)


class Command(LoggingCommand):
    help = "Optimize MySQL tables"  # NOQA: A003

    def handle(self, *args, **options):
        self.stdout.write("Optimizing MySQL tables")

        tables = [i for i in connection.introspection.table_names() if i.startswith("core_")]

        cursor = connection.cursor()

        for table in tables:
            self.stdout.write("Optimizing %s" % table)

            start_time = default_timer()
            cursor.execute("OPTIMIZE TABLE %s" % table)
            elapsed = default_timer() - start_time

            self.stdout.write("MySQL took %0.3f seconds to optimize %s" % (elapsed, table))
