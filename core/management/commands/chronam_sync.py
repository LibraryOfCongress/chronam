from __future__ import absolute_import

import os
from datetime import datetime
from optparse import make_option

from django.core import management

from chronam.core import index, models
from chronam.core.utils.utils import validate_bib_dir

from . import LoggingCommand


class Command(LoggingCommand):
    verbose = make_option("--verbose", action="store_true", dest="verbose", default=False, help="")

    skip_essays = make_option(
        "--skip-essays",
        action="store_true",
        dest="skip_essays",
        default=True,
        help="Skip essay loading.",
    )
    no_skip_essays = make_option(
        "--no-skip-essays",
        action="store_false",
        dest="skip_essays",
        help="Do not skip essay loading.",
    )

    pull_title_updates = make_option(
        "--pull-title-updates",
        action="store_true",
        dest="pull_title_updates",
        default=False,
        help="Pull down a new set of titles.",
    )

    option_list = LoggingCommand.option_list + (
        verbose,
        skip_essays,
        pull_title_updates,
    )
    help = ""  # NOQA: A003
    args = ""

    def handle(self, **options):
        if not (
            models.Title.objects.all().count() == 0
            and models.Holding.objects.all().count() == 0
            and models.Essay.objects.all().count() == 0
            and models.Batch.objects.all().count() == 0
            and models.Issue.objects.all().count() == 0
            and models.Page.objects.all().count() == 0
            and index.page_count() == 0
            and index.title_count() == 0
        ):
            self.stderr.write("Database or index not empty as expected.")
            return

        start = datetime.now()
        management.call_command("loaddata", "languages.json")
        management.call_command("loaddata", "institutions.json")
        management.call_command("loaddata", "ethnicities.json")
        management.call_command("loaddata", "labor_presses.json")
        management.call_command("loaddata", "countries.json")

        bib_in_settings = validate_bib_dir()
        if bib_in_settings:
            # look in BIB_STORAGE for original titles to load
            for filename in os.listdir(bib_in_settings):
                if filename.startswith("titles-") and filename.endswith(".xml"):
                    filepath = os.path.join(bib_in_settings, filename)
                    management.call_command("load_titles", filepath, skip_index=True)

        management.call_command(
            "title_sync",
            skip_essays=options["skip_essays"],
            pull_title_updates=options["pull_title_updates"],
        )

        end = datetime.now()
        total_time = end - start
        self.stdout.write("start time: %s" % start)
        self.stdout.write("end time: %s" % end)
        self.stdout.write("total time: %s" % total_time)
        self.stdout.write("chronam_sync done.")
