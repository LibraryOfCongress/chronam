from __future__ import absolute_import

import logging
from datetime import datetime
from optparse import make_option

from django.conf import settings

from chronam.core import title_pull

from . import LoggingCommand

LOGGER = logging.getLogger(__name__)


class Command(LoggingCommand):
    help = "Retrieve a fresh pull of titles from OCLC"  # NOQA: A003
    args = ""
    # TODO: Remove default from lccn
    option_list = LoggingCommand.option_list + (
        make_option(
            "-l",
            "--lccn",
            action="store",
            dest="lccn",
            default=None,
            help="Pass a specific lccn to pull down updates from Worldcat.",
        ),
        make_option(
            "-o",
            "--oclc",
            action="store",
            dest="oclc",
            default=None,
            help="Pass an oclc number when you pass an lccn.",
        ),
        make_option(
            "-p",
            "--path",
            action="store",
            dest="path",
            default="/worldcat_titles/",
            help="Path var that is appended to settings.BIB_STORAGE to save to",
        ),
    )

    def run_pull(self, path, lccn=None, oclc=None, query=None):
        start = datetime.now()
        search = title_pull.TitlePuller()
        save_path = settings.BIB_STORAGE + path
        search.run(save_path, lccn, oclc, query)
        end = datetime.now()
        return start, end

    def handle(self, **options):
        lccn = options["lccn"]
        oclc = options["oclc"]
        path = options["path"]

        if lccn:
            start, end = self.run_pull(path + "/lccn/", lccn, oclc)
            if start and end:
                LOGGER.info("lccn: %s, oclc: %s" % (lccn, oclc))
        else:
            LOGGER.info("started pulling titles from OCLC.")
            start, end = self.run_pull(path + "bulk/")
            LOGGER.info("finished pulling titles from OCLC.")
            LOGGER.info("start time: %s" % start)
            LOGGER.info("end time: %s" % end)

        total = end - start
        LOGGER.info("total time: %s" % total)
        LOGGER.info("#######################################")
