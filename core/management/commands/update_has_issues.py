from django.core.management.base import BaseCommand

from openoni.core import models as m
    
class Command(BaseCommand):
    help = "Updates the Title.has_issues property appropriately"

    def handle(self, *args, **options):
        q = m.Title.objects.filter(pk__in=m.Issue.objects.values("title"))
        q = q.distinct()
        for t in q:
            print "%s has issues" % t
            t.has_issues = True
            t.save()

