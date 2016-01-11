from django.core.management.base import BaseCommand

import json
from urllib import urlopen

from openoni.core.models import Batch

class Command(BaseCommand):
    help = "compares batches loaded with the public site"

    def handle(self, *args, **options):
        url = 'http://chroniclingamerica.loc.gov/batches.json'
        missing_batches = []
        missing_pages = []
        while url:
            batch_info = json.loads(urlopen(url).read())
            for batch in batch_info['batches']:
                print "comparing %(name)s with %(page_count)s pages" % batch
                try:
                    my_batch = Batch.objects.get(name=batch['name'])
                    if my_batch.page_count != batch['page_count']:
                        batch['my_page_count'] = my_batch.page_count
                        missing_pages.append(batch)
                except Batch.DoesNotExist: 
                    missing_batches.append(batch)
            url = batch_info.get('next', None) 

        if len(missing_batches) > 0:
            print "missing batches:"
            for batch in missing_batches:
                print "  %s" % batch['name']
            print

        if len(missing_pages) > 0:
            print "batches that are missing pages:"
            for batch in missing_pages:
                print "  %s has %s instead of %s pages" % (batch['name'],
                        batch['my_page_count'], batch['page_count'])
            print
