from django.core.management.base import BaseCommand
from django.conf import settings

from openoni.core.cts import CTS

class Command(BaseCommand):
    help = "list service requests that are in the queue"

    def handle(self, *args, **options):
        cts = CTS(settings.CTS_USERNAME, settings.CTS_PASSWORD, settings.CTS_URL)
        for sr in cts.get_service_requests(settings.CTS_QUEUE, 
                settings.CTS_SERVICE_TYPE):
            bag_instance_id = sr.data['requestParameters']['baginstancekey']
            bag = cts.get_bag_instance(bag_instance_id)
            bag_dir = bag.data['filepath']
            print "service request %s with status %s to load %s" % (sr.data['key'], sr.data['status'], bag_dir)

