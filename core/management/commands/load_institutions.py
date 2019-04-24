from __future__ import absolute_import

import codecs
import csv

from chronam.core.models import Institution

from . import LoggingCommand


"""
Loads the institutions based on a CSV file in the form of:
<code>, <name>, <city>, <state>, <zip>
"""


class Command(LoggingCommand):
    help = 'loads institution csv data into Institution table'  # NOQA: A003
    args = '<institution_csv_file>'

    def handle(self, csv_file, *args, **options):
        for row in unicode_csv_reader(codecs.open(csv_file, encoding='utf-8')):
            i = Institution()
            i.code = row[0].upper()
            i.name = row[1]
            i.address1 = ""
            i.address2 = ""
            i.city = row[2]
            i.state = row[3]
            i.zip = row[4]
            i.save()


# some hoops to get csv reader to emit unicode
# http://www.python.org/doc/2.5.2/lib/csv-examples.html


def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_encoder(unicode_csv_data), dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]


def utf8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')
