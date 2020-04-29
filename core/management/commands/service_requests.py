from __future__ import absolute_import, print_function

from django.conf import settings

from chronam.core.cts import CTS

from . import LoggingCommand


class Command(LoggingCommand):
    help = "list service requests that are in the queue"  # NOQA: A003

    def handle(self, *args, **options):
        cts = CTS(settings.CTS_USERNAME, settings.CTS_PASSWORD, settings.CTS_URL)
        for sr in cts.get_service_requests(settings.CTS_QUEUE, settings.CTS_SERVICE_TYPE):
            bag_instance_id = sr.data['requestParameters']['baginstancekey']
            bag = cts.get_bag_instance(bag_instance_id)
            bag_dir = bag.data['filepath']
            self.stdout.write(
                "service request %s with status %s to load %s" % (sr.data['key'], sr.data['status'], bag_dir)
            )
