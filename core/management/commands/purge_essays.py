from django.core.management.base import BaseCommand

from openoni.core.management.commands import configure_logging
from openoni.core.models import Essay
from openoni.core.essay_loader import purge_essay

configure_logging("purge_essays.config", 'purge_essays.log')


class Command(BaseCommand):
    help = "purge all the essays"

    def handle(self, *args, **options):
        for essay in Essay.objects.all():
            purge_essay(essay.essay_editor_url)
