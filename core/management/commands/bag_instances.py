from django.core.management.base import BaseCommand
from django.conf import settings

from openoni.core.cts import CTS

class Command(BaseCommand):
    help = "Lookup CTS bag_instance ids for batches"

    def handle(self, *args, **options):
        cts = CTS(settings.CTS_USERNAME, settings.CTS_PASSWORD, settings.CTS_URL)
        ndnp = cts.get_project(settings.CTS_PROJECT_ID)

        for bag in ndnp.get_bags():
            for instance in bag.get_bag_instances():
                for instance_type in instance.data['bagInstanceTypes']:
                    if instance_type['name'] == 'public access':
                        print instance.data['filepath']
