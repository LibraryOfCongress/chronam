# encoding: utf-8
"""
Dump IIIF Image API base URLs for random pages
"""

from __future__ import absolute_import, print_function

from urllib import quote

from django.conf import settings

from chronam.core.models import Page

from . import LoggingCommand


class Command(LoggingCommand):
    help = __doc__.strip()  # NOQA: A003
    args = "<count>"

    def handle(self, *args, **options):
        if len(args) != 1:
            self.stderr.write("Using the first 500 items")
            limit = 500
        else:
            limit = int(args[0])

        pages = (
            Page.objects.exclude(jp2_filename=None)
            .order_by("?")
            .values_list("issue__batch__name", "jp2_filename")
        )

        pages = pages[:limit]

        for batch_name, jp2_filename in pages.iterator():
            identifier = quote("%s/data/%s" % (batch_name, jp2_filename), safe="")
            self.stdout.write("%s/%s/info.json" % (settings.IIIF_IMAGE_BASE_URL.rstrip("/"), identifier))
