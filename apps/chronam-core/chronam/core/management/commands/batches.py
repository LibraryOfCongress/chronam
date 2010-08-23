from optparse import make_option

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from chronam.web import models
    
class Command(BaseCommand):
    help = "Displays information about batches"
    args = ''

    def handle(self, *args, **options):
        batches = models.Batch.objects.all()
        for batch in models.Batch.objects.all().order_by('name'):
            print batch.name
