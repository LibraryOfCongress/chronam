from __future__ import absolute_import

from chronam.core.essay_loader import purge_essay
from chronam.core.models import Essay

from . import LoggingCommand


class Command(LoggingCommand):
    help = "purge all the essays"

    def handle(self, *args, **options):
        for essay in Essay.objects.all():
            purge_essay(essay.essay_editor_url)
