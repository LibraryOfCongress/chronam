from django.core.management.base import BaseCommand

from openoni.core import models
    
class Command(BaseCommand):

    def handle(self, *args, **options):
        for e in models.Ethnicity.objects.all():
            print e.name, ": ", e.has_issues
