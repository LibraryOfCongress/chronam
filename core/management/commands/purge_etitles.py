import logging

from cStringIO import StringIO
from optparse import make_option

from django.core.management.base import BaseCommand
import pymarc

from openoni.core.management.commands import configure_logging
from openoni.core import index
from openoni.core.models import Title

configure_logging("openoni_purge_titles.config", "openoni_purge_etitles.log")
_log = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Management command for purging title records which have an 856 field 
    containing a link to Chronicling America, and which appear to be records 
    for an electronic only version of a title 245 $h == [electronic resource].

    The script is careful not to purge any records that have issues attached 
    to them.  See https://rdc.lctl.gov/trac/ndnp/ticket/375 for context.

    If you want to see the records that will be purged use the --pretend
    option.
    """

    option_list = BaseCommand.option_list + (
        make_option('-p', '--pretend', dest='pretend', action='store_true'),
    )

    def handle(self, **options):
        for title in Title.objects.filter(urls__value__icontains=
                'chroniclingamerica'):
            record = pymarc.parse_xml_to_array(StringIO(title.marc.xml))[0]
            if record['245']['h'] == '[electronic resource].':
                if options['pretend']:
                    print title
                else:
                    _log.info("deleting %s [%s] from solr index")
                    index.delete_title(title)
                    _log.info("purging %s [%s]" % (title, title.lccn))
                    title.delete()
        if not options['pretend']:
            index.commit()
