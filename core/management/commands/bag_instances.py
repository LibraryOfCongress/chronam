from __future__ import absolute_import, print_function

from django.conf import settings

from chronam.core.cts import CTS

from . import LoggingCommand


class Command(LoggingCommand):
    help = "Lookup CTS bag_instance ids for batches"  # NOQA: A003

    def handle(self, *args, **options):
        cts = CTS(settings.CTS_USERNAME, settings.CTS_PASSWORD, settings.CTS_URL)
        ndnp = cts.get_project(settings.CTS_PROJECT_ID)

        for bag in ndnp.get_bags():
            for instance in bag.get_bag_instances():
                for instance_type in instance.data['bagInstanceTypes']:
                    if instance_type['name'] == 'public access':
                        self.stdout.write(instance.data['filepath'])
