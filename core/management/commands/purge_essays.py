from __future__ import absolute_import

from django.core.management.base import BaseCommand

from chronam.core.essay_loader import purge_essay
from chronam.core.models import Essay


class Command(BaseCommand):
    help = "purge all the essays"

    def handle(self, *args, **options):
        for essay in Essay.objects.all():
            purge_essay(essay.essay_editor_url)
